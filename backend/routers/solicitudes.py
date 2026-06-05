from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user, require_roles
import models
import schemas

router = APIRouter(prefix="/api/solicitudes", tags=["solicitudes"])


def _build_solicitud_out(solicitud: models.Solicitud) -> dict:
    detalles = []
    total = 0.0
    for d in solicitud.detalles:
        qty = d.cantidad_aprobada if d.cantidad_aprobada is not None else d.cantidad_solicitada
        subtotal = round(qty * d.precio_unitario_snapshot, 2)
        total += subtotal
        detalles.append({
            "id": d.id,
            "material_id": d.material_id,
            "material_codigo": d.material.codigo if d.material else None,
            "material_nombre": d.material.nombre if d.material else "—",
            "material_unidad": d.material.unidad_medida if d.material else "",
            "cantidad_solicitada": d.cantidad_solicitada,
            "cantidad_aprobada": d.cantidad_aprobada,
            "precio_unitario_snapshot": d.precio_unitario_snapshot,
            "subtotal": subtotal,
            "material_stock_actual": d.material.stock_actual if d.material else None,
        })
    return {
        "id": solicitud.id,
        "solicitante_id": solicitud.solicitante_id,
        "solicitante_nombre": solicitud.solicitante.nombre if solicitud.solicitante else "—",
        "linea_produccion_id": solicitud.linea_produccion_id,
        "linea_produccion_nombre": solicitud.linea_produccion.nombre if solicitud.linea_produccion else "—",
        "estado": solicitud.estado,
        "observaciones": solicitud.observaciones,
        "fecha_requerida": solicitud.fecha_requerida,
        "created_at": solicitud.created_at,
        "updated_at": solicitud.updated_at,
        "detalles": detalles,
        "total": round(total, 2),
    }


@router.get("/", response_model=list[schemas.SolicitudResumen])
def list_solicitudes(
    estado: str = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    q = db.query(models.Solicitud)

    # Solicitantes solo ven sus propias solicitudes
    if current_user.rol == "solicitante":
        q = q.filter(models.Solicitud.solicitante_id == current_user.id)

    if estado:
        q = q.filter(models.Solicitud.estado == estado)

    solicitudes = q.order_by(models.Solicitud.created_at.desc()).all()

    result = []
    for s in solicitudes:
        total = sum(
            (d.cantidad_aprobada if d.cantidad_aprobada is not None else d.cantidad_solicitada)
            * d.precio_unitario_snapshot
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


@router.get("/{solicitud_id}", response_model=schemas.SolicitudOut)
def get_solicitud(
    solicitud_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    solicitud = db.query(models.Solicitud).filter(models.Solicitud.id == solicitud_id).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    # Solicitante solo puede ver sus propias solicitudes
    if current_user.rol == "solicitante" and solicitud.solicitante_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    return _build_solicitud_out(solicitud)


@router.post("/", response_model=schemas.SolicitudOut)
def create_solicitud(
    data: schemas.SolicitudCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_roles("solicitante")),
):
    linea = db.query(models.LineaProduccion).filter(
        models.LineaProduccion.id == data.linea_produccion_id,
        models.LineaProduccion.activo == True,
    ).first()
    if not linea:
        raise HTTPException(status_code=404, detail="Línea de producción no encontrada")

    solicitud = models.Solicitud(
        solicitante_id=current_user.id,
        linea_produccion_id=data.linea_produccion_id,
        estado="pendiente",
        observaciones=data.observaciones,
        fecha_requerida=data.fecha_requerida,
    )
    db.add(solicitud)
    db.flush()  # para obtener el ID antes del commit

    for item in data.items:
        material = db.query(models.Material).filter(
            models.Material.id == item.material_id,
            models.Material.activo == True,
        ).first()
        if not material:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Material ID {item.material_id} no encontrado o inactivo")

        detalle = models.DetalleSolicitud(
            solicitud_id=solicitud.id,
            material_id=material.id,
            cantidad_solicitada=item.cantidad_solicitada,
            precio_unitario_snapshot=material.precio_unitario,  # snapshot del precio actual
        )
        db.add(detalle)

    # Registro en historial
    historial = models.HistorialEstados(
        solicitud_id=solicitud.id,
        estado_anterior=None,
        estado_nuevo="pendiente",
        usuario_id=current_user.id,
        comentario="Solicitud creada",
    )
    db.add(historial)
    db.commit()
    db.refresh(solicitud)

    return _build_solicitud_out(solicitud)


@router.get("/{solicitud_id}/historial", response_model=list[schemas.HistorialOut])
def get_historial(
    solicitud_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    solicitud = db.query(models.Solicitud).filter(models.Solicitud.id == solicitud_id).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    historial = db.query(models.HistorialEstados).filter(
        models.HistorialEstados.solicitud_id == solicitud_id
    ).order_by(models.HistorialEstados.created_at).all()

    return [
        {
            "id": h.id,
            "estado_anterior": h.estado_anterior,
            "estado_nuevo": h.estado_nuevo,
            "usuario_nombre": h.usuario.nombre if h.usuario else "—",
            "comentario": h.comentario,
            "created_at": h.created_at,
        }
        for h in historial
    ]
