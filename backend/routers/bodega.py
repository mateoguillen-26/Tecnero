import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import require_roles
from routers.materiales import verificar_y_crear_alerta
import models
import schemas

router = APIRouter(prefix="/api/bodega", tags=["bodega"])


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
        raise HTTPException(status_code=400, detail=f"Solo se pueden entregar solicitudes aprobadas (estado actual: {solicitud.estado})")

    materiales_afectados = []
    for detalle in solicitud.detalles:
        if detalle.cantidad_aprobada and detalle.cantidad_aprobada > 0:
            material = db.query(models.Material).filter(models.Material.id == detalle.material_id).first()
            if material:
                material.stock_actual = max(0.0, material.stock_actual - detalle.cantidad_aprobada)
                material.updated_at = datetime.datetime.utcnow()
                materiales_afectados.append(material)

    solicitud.estado = "entregada"
    solicitud.updated_at = datetime.datetime.utcnow()

    historial = models.HistorialEstados(
        solicitud_id=solicitud.id,
        estado_anterior="aprobada",
        estado_nuevo="entregada",
        usuario_id=current_user.id,
        comentario="Materiales entregados desde bodega",
    )
    db.add(historial)
    db.commit()

    # Verificar alertas DESPUÉS del commit para que los nuevos stocks estén guardados
    for material in materiales_afectados:
        db.refresh(material)
        verificar_y_crear_alerta(db, material)

    return {"detail": "Solicitud marcada como entregada y stock descontado correctamente"}
