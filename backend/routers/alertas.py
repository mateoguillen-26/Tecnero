from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user, require_roles
import models
import schemas

router = APIRouter(prefix="/api/alertas", tags=["alertas"])


@router.get("/", response_model=list[schemas.AlertaOut])
def list_alertas(
    solo_activas: bool = True,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    q = db.query(models.Alerta)
    if solo_activas:
        q = q.filter(models.Alerta.activa == True)
    alertas = q.order_by(models.Alerta.created_at.desc()).all()

    return [
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
        for a in alertas
    ]


@router.post("/{alerta_id}/resolver")
def resolver_alerta(
    alerta_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_roles("coordinador", "bodeguero")),
):
    alerta = db.query(models.Alerta).filter(models.Alerta.id == alerta_id).first()
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")

    alerta.activa = False
    db.commit()
    return {"detail": "Alerta resuelta manualmente"}
