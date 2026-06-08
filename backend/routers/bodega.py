import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
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
        models.Solicitud.estado == "aprobada",
        models.Solicitud.tipo == "requerimiento",
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
            "tipo": s.tipo or "requerimiento",
            "proveedor": s.proveedor,
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


# ═══════════════════════════════════════════════════════════════════════════════
# PEDIDOS DE COMPRA
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/pedidos")
def crear_pedido(
    data: schemas.PedidoCompraCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_roles("bodeguero")),
):
    """Bodeguero crea un pedido de compra para reponer stock."""
    pedido = models.Solicitud(
        solicitante_id=current_user.id,
        linea_produccion_id=None,
        tipo="pedido_compra",
        estado="pendiente",
        proveedor=data.proveedor,
        observaciones=data.observaciones,
        fecha_requerida=None,
    )
    db.add(pedido)
    db.flush()

    for item in data.items:
        material = db.query(models.Material).filter(
            models.Material.id == item.material_id,
            models.Material.activo == True,
        ).first()
        if not material:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Material ID {item.material_id} no encontrado")

        detalle = models.DetalleSolicitud(
            solicitud_id=pedido.id,
            material_id=material.id,
            cantidad_solicitada=item.cantidad,
            precio_unitario_snapshot=material.precio_unitario,
        )
        db.add(detalle)

    db.add(models.HistorialEstados(
        solicitud_id=pedido.id,
        estado_anterior=None,
        estado_nuevo="pendiente",
        usuario_id=current_user.id,
        comentario="Pedido de compra creado",
    ))
    db.commit()
    db.refresh(pedido)
    return {"detail": "Pedido de compra creado correctamente", "id": pedido.id}


@router.get("/pedidos/lista")
def list_pedidos(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_roles("bodeguero")),
):
    """Lista todos los pedidos de compra (cualquier estado)."""
    pedidos = db.query(models.Solicitud).filter(
        models.Solicitud.tipo == "pedido_compra"
    ).order_by(models.Solicitud.created_at.desc()).all()

    result = []
    for p in pedidos:
        total = sum(
            (d.cantidad_aprobada or d.cantidad_solicitada) * d.precio_unitario_snapshot
            for d in p.detalles
        )
        result.append({
            "id": p.id,
            "estado": p.estado,
            "proveedor": p.proveedor or "—",
            "observaciones": p.observaciones,
            "created_at": p.created_at,
            "num_items": len(p.detalles),
            "total": round(total, 2),
            "items_resumen": [
                {
                    "material_nombre": d.material.nombre if d.material else "—",
                    "material_codigo": d.material.codigo if d.material else "—",
                    "cantidad_solicitada": d.cantidad_solicitada,
                    "cantidad_aprobada": d.cantidad_aprobada,
                    "unidad": d.material.unidad_medida if d.material else "",
                }
                for d in p.detalles
            ],
        })
    return result


@router.post("/pedidos/{pedido_id}/recibir")
def recibir_pedido(
    pedido_id: int,
    data: schemas.RecepcionRequest,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_roles("bodeguero")),
):
    """Bodeguero confirma recepción física → stock aumenta por cantidad aprobada."""
    pedido = db.query(models.Solicitud).filter(
        models.Solicitud.id == pedido_id,
        models.Solicitud.tipo == "pedido_compra",
    ).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido de compra no encontrado")
    if pedido.estado != "aprobada":
        raise HTTPException(
            status_code=400,
            detail=f"Solo se pueden recibir pedidos aprobados (estado actual: {pedido.estado})"
        )

    materiales_afectados = []
    for detalle in pedido.detalles:
        cant = detalle.cantidad_aprobada or 0
        if cant <= 0:
            continue
        material = db.query(models.Material).filter(models.Material.id == detalle.material_id).first()
        if material:
            material.stock_actual = round(material.stock_actual + cant, 4)
            material.updated_at = datetime.datetime.utcnow()
            materiales_afectados.append(material)

    pedido.estado = "recibida"
    pedido.updated_at = datetime.datetime.utcnow()

    db.add(models.HistorialEstados(
        solicitud_id=pedido.id,
        estado_anterior="aprobada",
        estado_nuevo="recibida",
        usuario_id=current_user.id,
        comentario=data.comentario or "Materiales recibidos en bodega — stock actualizado",
    ))
    db.commit()

    for material in materiales_afectados:
        db.refresh(material)
        verificar_y_crear_alerta(db, material)

    return {"detail": f"Recepción confirmada. Stock actualizado en {len(materiales_afectados)} material(es)."}
