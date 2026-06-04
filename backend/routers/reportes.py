import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
import models

router = APIRouter(prefix="/api/reportes", tags=["reportes"])


@router.get("/lineas")
def reporte_lineas(
    fecha_inicio: str = Query(None),
    fecha_fin: str = Query(None),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    """Reporte de gasto por línea de producción, desglosado por material."""
    hoy = datetime.datetime.utcnow()
    inicio = datetime.datetime.fromisoformat(fecha_inicio) if fecha_inicio else hoy.replace(day=1, hour=0, minute=0, second=0)
    fin = datetime.datetime.fromisoformat(fecha_fin) if fecha_fin else hoy

    solicitudes = db.query(models.Solicitud).filter(
        models.Solicitud.created_at >= inicio,
        models.Solicitud.created_at <= fin,
        models.Solicitud.estado.in_(["aprobada", "entregada"]),
    ).all()

    # Estructura: { linea: { material: {cantidad, valor} } }
    reporte: dict = {}
    for s in solicitudes:
        linea = s.linea_produccion.nombre if s.linea_produccion else "Desconocida"
        if linea not in reporte:
            reporte[linea] = {}
        for d in s.detalles:
            mat = d.material.nombre if d.material else "—"
            unidad = d.material.unidad_medida if d.material else ""
            qty = d.cantidad_aprobada or d.cantidad_solicitada
            valor = qty * d.precio_unitario_snapshot
            if mat not in reporte[linea]:
                reporte[linea][mat] = {"material": mat, "unidad": unidad, "cantidad": 0.0, "valor": 0.0}
            reporte[linea][mat]["cantidad"] += qty
            reporte[linea][mat]["valor"] += valor

    total_general = 0.0
    resultado = []
    for linea, materiales in reporte.items():
        items = list(materiales.values())
        for item in items:
            item["valor"] = round(item["valor"], 2)
            item["cantidad"] = round(item["cantidad"], 2)
        total_linea = sum(i["valor"] for i in items)
        total_general += total_linea
        resultado.append({"linea": linea, "materiales": sorted(items, key=lambda x: x["valor"], reverse=True), "total": round(total_linea, 2)})

    resultado.sort(key=lambda x: x["total"], reverse=True)

    # Agregar porcentajes
    for item in resultado:
        item["porcentaje"] = round((item["total"] / total_general * 100) if total_general > 0 else 0, 1)

    return {
        "fecha_inicio": inicio.isoformat(),
        "fecha_fin": fin.isoformat(),
        "lineas": resultado,
        "total_general": round(total_general, 2),
    }


@router.get("/material/{material_id}")
def reporte_material(
    material_id: int,
    fecha_inicio: str = Query(None),
    fecha_fin: str = Query(None),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    """Historial de solicitudes para un material específico."""
    material = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not material:
        return {"error": "Material no encontrado"}

    hoy = datetime.datetime.utcnow()
    inicio = datetime.datetime.fromisoformat(fecha_inicio) if fecha_inicio else hoy.replace(year=hoy.year - 1)
    fin = datetime.datetime.fromisoformat(fecha_fin) if fecha_fin else hoy

    detalles = db.query(models.DetalleSolicitud).join(models.Solicitud).filter(
        models.DetalleSolicitud.material_id == material_id,
        models.Solicitud.created_at >= inicio,
        models.Solicitud.created_at <= fin,
    ).order_by(models.Solicitud.created_at.desc()).all()

    registros = []
    total_cantidad = 0.0
    total_valor = 0.0
    for d in detalles:
        qty = d.cantidad_aprobada or d.cantidad_solicitada
        valor = qty * d.precio_unitario_snapshot
        total_cantidad += qty
        total_valor += valor
        registros.append({
            "solicitud_id": d.solicitud_id,
            "fecha": d.solicitud.created_at.isoformat(),
            "solicitante": d.solicitud.solicitante.nombre if d.solicitud.solicitante else "—",
            "linea": d.solicitud.linea_produccion.nombre if d.solicitud.linea_produccion else "—",
            "estado": d.solicitud.estado,
            "cantidad_solicitada": d.cantidad_solicitada,
            "cantidad_aprobada": d.cantidad_aprobada,
            "precio_snapshot": d.precio_unitario_snapshot,
            "valor": round(valor, 2),
        })

    return {
        "material": material.nombre,
        "unidad": material.unidad_medida,
        "fecha_inicio": inicio.isoformat(),
        "fecha_fin": fin.isoformat(),
        "registros": registros,
        "total_cantidad": round(total_cantidad, 2),
        "total_valor": round(total_valor, 2),
    }


@router.get("/inventario")
def reporte_inventario(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    """Estado actual de inventario con valor total."""
    materiales = db.query(models.Material).filter(models.Material.activo == True).order_by(models.Material.nombre).all()

    items = []
    valor_total = 0.0
    for m in materiales:
        valor = m.stock_actual * m.precio_unitario
        valor_total += valor
        if m.stock_actual <= 0:
            estado = "sin_stock"
        elif m.stock_actual <= m.stock_minimo:
            estado = "bajo"
        else:
            estado = "normal"
        items.append({
            "id": m.id,
            "codigo": m.codigo,
            "nombre": m.nombre,
            "unidad_medida": m.unidad_medida,
            "precio_unitario": m.precio_unitario,
            "stock_actual": m.stock_actual,
            "stock_minimo": m.stock_minimo,
            "valor_total": round(valor, 2),
            "estado": estado,
        })

    return {
        "generado_en": datetime.datetime.utcnow().isoformat(),
        "materiales": items,
        "valor_total_inventario": round(valor_total, 2),
        "total_items": len(items),
    }
