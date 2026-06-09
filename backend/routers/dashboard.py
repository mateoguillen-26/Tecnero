import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from auth import get_current_user
import models
import schemas

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/", response_model=schemas.DashboardOut)
def get_dashboard(
    fecha_inicio: str = Query(None),
    fecha_fin: str = Query(None),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    hoy = datetime.datetime.utcnow()

    # Rango de fechas por defecto: mes actual
    if fecha_inicio:
        inicio = datetime.datetime.fromisoformat(fecha_inicio)
    else:
        inicio = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if fecha_fin:
        fin = datetime.datetime.fromisoformat(fecha_fin)
    else:
        fin = hoy

    # ─── KPIs ────────────────────────────────────────────────────────────────
    total_sol_mes = db.query(models.Solicitud).filter(
        models.Solicitud.tipo == "requerimiento",
        models.Solicitud.created_at >= inicio,
        models.Solicitud.created_at <= fin,
    ).count()

    # Monto total del mes (requerimientos aprobados + entregados)
    solicitudes_mes = db.query(models.Solicitud).filter(
        models.Solicitud.tipo == "requerimiento",
        models.Solicitud.created_at >= inicio,
        models.Solicitud.created_at <= fin,
        models.Solicitud.estado.in_(["aprobada", "entregada"]),
    ).all()

    monto_mes = 0.0
    for s in solicitudes_mes:
        for d in s.detalles:
            qty = d.cantidad_aprobada or d.cantidad_solicitada
            monto_mes += qty * d.precio_unitario_snapshot

    sol_pendientes = db.query(models.Solicitud).filter(
        models.Solicitud.tipo == "requerimiento",
        models.Solicitud.estado == "pendiente",
    ).count()

    alertas_activas_count = db.query(models.Alerta).filter(models.Alerta.activa == True).count()

    # ─── Gasto por línea de producción ───────────────────────────────────────
    solicitudes_rango = db.query(models.Solicitud).filter(
        models.Solicitud.tipo == "requerimiento",
        models.Solicitud.created_at >= inicio,
        models.Solicitud.created_at <= fin,
        models.Solicitud.estado.in_(["aprobada", "entregada"]),
    ).all()

    gasto_lineas: dict[str, float] = {}
    for s in solicitudes_rango:
        linea_nombre = s.linea_produccion.nombre if s.linea_produccion else "Desconocida"
        for d in s.detalles:
            qty = d.cantidad_aprobada or d.cantidad_solicitada
            gasto_lineas[linea_nombre] = gasto_lineas.get(linea_nombre, 0.0) + qty * d.precio_unitario_snapshot

    total_gasto = sum(gasto_lineas.values())
    gasto_por_linea = [
        {
            "linea": k,
            "total": round(v, 2),
            "porcentaje": round((v / total_gasto * 100) if total_gasto > 0 else 0, 1),
        }
        for k, v in sorted(gasto_lineas.items(), key=lambda x: x[1], reverse=True)
    ]

    # ─── Top 5 materiales ────────────────────────────────────────────────────
    materiales_stats: dict[int, dict] = {}
    for s in solicitudes_rango:
        for d in s.detalles:
            mid = d.material_id
            qty = d.cantidad_aprobada or d.cantidad_solicitada
            if mid not in materiales_stats:
                materiales_stats[mid] = {
                    "nombre": d.material.nombre if d.material else "—",
                    "unidad": d.material.unidad_medida if d.material else "",
                    "total_valor": 0.0,
                    "total_cantidad": 0.0,
                }
            materiales_stats[mid]["total_valor"] += qty * d.precio_unitario_snapshot
            materiales_stats[mid]["total_cantidad"] += qty

    top_materiales = sorted(materiales_stats.values(), key=lambda x: x["total_valor"], reverse=True)[:5]
    top_materiales = [
        {
            "material": m["nombre"],
            "unidad": m["unidad"],
            "total_valor": round(m["total_valor"], 2),
            "total_cantidad": round(m["total_cantidad"], 2),
        }
        for m in top_materiales
    ]

    # ─── Inventario (todos los materiales activos) ───────────────────────────
    materiales = db.query(models.Material).filter(models.Material.activo == True).order_by(models.Material.nombre).all()
    inventario = []
    for m in materiales:
        if m.stock_actual <= 0:
            estado = "sin_stock"
        elif m.stock_actual <= m.stock_minimo:
            estado = "bajo"
        else:
            estado = "normal"
        inventario.append({
            "id": m.id,
            "nombre": m.nombre,
            "unidad_medida": m.unidad_medida,
            "stock_actual": m.stock_actual,
            "stock_minimo": m.stock_minimo,
            "estado": estado,
            "precio_unitario": m.precio_unitario,
        })

    # ─── Alertas activas ─────────────────────────────────────────────────────
    alertas_raw = db.query(models.Alerta).filter(models.Alerta.activa == True).all()
    alertas = [
        {
            "id": a.id,
            "material_id": a.material_id,
            "material_nombre": a.material.nombre if a.material else "—",
            "tipo": a.tipo,
            "mensaje": a.mensaje,
            "activa": a.activa,
            "created_at": a.created_at,
            "stock_actual": a.material.stock_actual if a.material else 0,
            "stock_minimo": a.material.stock_minimo if a.material else 0,
        }
        for a in alertas_raw
    ]

    return {
        "kpis": {
            "total_solicitudes_mes": total_sol_mes,
            "monto_total_mes": round(monto_mes, 2),
            "solicitudes_pendientes": sol_pendientes,
            "alertas_activas": alertas_activas_count,
        },
        "gasto_por_linea": gasto_por_linea,
        "top_materiales": top_materiales,
        "inventario": inventario,
        "alertas": alertas,
    }
