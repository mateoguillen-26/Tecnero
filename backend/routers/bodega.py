import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import require_roles
from routers.materiales import verificar_y_crear_alerta
import models
import schemas

router = APIRouter(prefix="/api/bodega", tags=["bodega"])


def _verificar_stock_solicitud(db: Session, solicitud: models.Solicitud) -> list[dict]:
    """
    Revisa si hay stock suficiente para todos los ítems aprobados.
    Retorna lista de faltantes (vacía = todo OK).
    """
    faltantes = []
    for detalle in solicitud.detalles:
        cant = detalle.cantidad_aprobada or 0
        if cant <= 0:
            continue
        material = db.query(models.Material).filter(models.Material.id == detalle.material_id).first()
        if not material:
            continue
        if material.stock_actual < cant:
            faltantes.append({
                "codigo": material.codigo,
                "nombre": material.nombre,
                "unidad": material.unidad_medida,
                "stock_disponible": material.stock_actual,
                "cantidad_necesaria": cant,
                "faltante": round(cant - material.stock_actual, 4),
            })
    return faltantes


@router.get("/aprobadas", response_model=list[schemas.SolicitudResumen])
def get_aprobadas(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_roles("bodeguero")),
):
    solicitudes = db.query(models.Solicitud).filter(
        models.Solicitud.estado == "aprobada"
    ).order_by(models.Solicitud.updated_at).all()

    result = []
    for s in solicitudes:
        total = sum(
            (d.cantidad_aprobada or 0) * d.precio_unitario_snapshot
            for d in s.detalles
        )
        result.append({
            "id": s.id,
            "solicitante_nombre": s.solicitante.nombre if s.solicitante else "—",
            "linea_produccion_nombre": s.linea_produccion.nombre if s.linea_produccion else "—",
            "estado": s.estado,
            "fecha_requerida": s.fecha_requerida,
            "created_at": s.created_at,
            "total": round(total, 2),
            "num_items": len(s.detalles),
        })
    return result


@router.get("/{solicitud_id}/verificar-stock")
def verificar_stock(
    solicitud_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_roles("bodeguero")),
):
    """Verifica si hay stock suficiente para despachar una solicitud aprobada."""
    solicitud = db.query(models.Solicitud).filter(models.Solicitud.id == solicitud_id).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    faltantes = _verificar_stock_solicitud(db, solicitud)
    return {
        "solicitud_id": solicitud_id,
        "stock_suficiente": len(faltantes) == 0,
        "faltantes": faltantes,
    }


@router.post("/{solicitud_id}/entregar")
def marcar_entregada(
    solicitud_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_roles("bodeguero")),
):
    solicitud = db.query(models.Solicitud).filter(models.Solicitud.id == solicitud_id).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if solicitud.estado != "aprobada":
        raise HTTPException(
            status_code=400,
            detail=f"Solo se pueden entregar solicitudes aprobadas (estado actual: {solicitud.estado})"
        )

    # ── Validación de stock ANTES de modificar nada ───────────────────────────
    faltantes = _verificar_stock_solicitud(db, solicitud)
    if faltantes:
        items_detalle = "; ".join([
            f"{f['codigo']} {f['nombre']}: necesita {f['cantidad_necesaria']} {f['unidad']}, "
            f"disponible {f['stock_disponible']} (faltan {f['faltante']})"
            for f in faltantes
        ])
        raise HTTPException(
            status_code=400,
            detail=f"No se puede despachar: stock insuficiente en {len(faltantes)} material(es). {items_detalle}"
        )

    # ── Descontar stock ───────────────────────────────────────────────────────
    materiales_afectados = []
    for detalle in solicitud.detalles:
        cant = detalle.cantidad_aprobada or 0
        if cant <= 0:
            continue
        material = db.query(models.Material).filter(models.Material.id == detalle.material_id).first()
        if material:
            material.stock_actual = round(material.stock_actual - cant, 4)
            material.updated_at = datetime.datetime.utcnow()
            materiales_afectados.append(material)

    solicitud.estado = "entregada"
    solicitud.updated_at = datetime.datetime.utcnow()

    db.add(models.HistorialEstados(
        solicitud_id=solicitud.id,
        estado_anterior="aprobada",
        estado_nuevo="entregada",
        usuario_id=current_user.id,
        comentario="Materiales entregados desde bodega",
    ))
    db.commit()

    # Verificar alertas después del descuento
    for material in materiales_afectados:
        db.refresh(material)
        verificar_y_crear_alerta(db, material)

    return {"detail": "Solicitud marcada como entregada y stock descontado correctamente"}
