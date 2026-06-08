import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import require_roles
from routers.materiales import verificar_y_crear_alerta
import models
import schemas

router = APIRouter(prefix="/api/aprobaciones", tags=["aprobaciones"])


@router.get("/pendientes", response_model=list[schemas.SolicitudResumen])
def get_pendientes(
    tipo: str = "requerimiento",
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_roles("coordinador")),
):
    solicitudes = db.query(models.Solicitud).filter(
        models.Solicitud.estado == "pendiente",
        models.Solicitud.tipo == tipo,
    ).order_by(models.Solicitud.created_at).all()

    result = []
    for s in solicitudes:
        total = sum(d.cantidad_solicitada * d.precio_unitario_snapshot for d in s.detalles)
        result.append({
            "id": s.id,
            "solicitante_nombre": s.solicitante.nombre if s.solicitante else "—",
            "linea_produccion_nombre": s.linea_produccion.nombre if s.linea_produccion else "—",
            "tipo": s.tipo,
            "proveedor": s.proveedor,
            "estado": s.estado,
            "fecha_requerida": s.fecha_requerida,
            "created_at": s.created_at,
            "total": round(total, 2),
            "num_items": len(s.detalles),
        })
    return result


@router.post("/{solicitud_id}")
def procesar_aprobacion(
    solicitud_id: int,
    data: schemas.AprobacionRequest,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_roles("coordinador")),
):
    solicitud = db.query(models.Solicitud).filter(models.Solicitud.id == solicitud_id).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if solicitud.estado != "pendiente":
        raise HTTPException(status_code=400, detail=f"Solo se pueden procesar solicitudes pendientes (estado actual: {solicitud.estado})")

    estado_anterior = solicitud.estado

    if data.accion == "rechazar":
        solicitud.estado = "rechazada"
        comentario = data.comentario or "Solicitud rechazada"

    elif data.accion == "aprobar":
        # Actualizar cantidades aprobadas (común a ambos tipos)
        if data.items:
            items_map = {item.detalle_id: item.cantidad_aprobada for item in data.items}
            for detalle in solicitud.detalles:
                detalle.cantidad_aprobada = items_map.get(detalle.id, detalle.cantidad_solicitada)
        else:
            for detalle in solicitud.detalles:
                detalle.cantidad_aprobada = detalle.cantidad_solicitada

        if solicitud.tipo == "pedido_compra":
            # Pedido de compra: aumentar stock inmediatamente → no pasa por el bodeguero
            solicitud.estado = "recibida"
            comentario = data.comentario or "Pedido de compra aprobado — stock actualizado"
            for detalle in solicitud.detalles:
                cant = detalle.cantidad_aprobada or 0
                if cant <= 0:
                    continue
                material = db.query(models.Material).filter(models.Material.id == detalle.material_id).first()
                if material:
                    material.stock_actual = round(material.stock_actual + cant, 4)
                    material.updated_at = datetime.datetime.utcnow()
        else:
            # Requerimiento de producción: flujo normal, bodeguero despacha
            solicitud.estado = "aprobada"
            comentario = data.comentario or "Solicitud aprobada"

    solicitud.updated_at = datetime.datetime.utcnow()

    historial = models.HistorialEstados(
        solicitud_id=solicitud.id,
        estado_anterior=estado_anterior,
        estado_nuevo=solicitud.estado,
        usuario_id=current_user.id,
        comentario=comentario,
    )
    db.add(historial)
    db.commit()

    # Post-commit: alertas y advertencias según tipo
    if solicitud.tipo == "pedido_compra" and solicitud.estado == "recibida":
        # Verificar alertas tras aumento de stock (puede desactivarlas si ya hay suficiente)
        materiales_ids = [d.material_id for d in solicitud.detalles]
        for mid in materiales_ids:
            mat = db.query(models.Material).filter(models.Material.id == mid).first()
            if mat:
                db.refresh(mat)
                verificar_y_crear_alerta(db, mat)
        return {"detail": "Pedido de compra aprobado y stock actualizado correctamente", "estado": solicitud.estado}

    # Advertencias de stock para requerimientos (informativas, no bloquean)
    avisos_stock = []
    if solicitud.estado == "aprobada":
        for detalle in solicitud.detalles:
            cant = detalle.cantidad_aprobada or 0
            if cant <= 0:
                continue
            material = db.query(models.Material).filter(models.Material.id == detalle.material_id).first()
            if material and material.stock_actual < cant:
                avisos_stock.append(
                    f"{material.codigo} {material.nombre}: stock actual {material.stock_actual} {material.unidad_medida} "
                    f"(aprobado {cant})"
                )

    respuesta = {"detail": f"Solicitud {solicitud.estado} correctamente", "estado": solicitud.estado}
    if avisos_stock:
        respuesta["avisos_stock"] = avisos_stock
        respuesta["advertencia"] = (
            f"Atención: {len(avisos_stock)} material(es) con stock insuficiente al momento de aprobar. "
            "El bodeguero no podrá despachar hasta que haya stock disponible."
        )
    return respuesta
