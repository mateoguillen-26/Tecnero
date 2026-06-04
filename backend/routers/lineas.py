from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
import models
import schemas

router = APIRouter(prefix="/api/lineas", tags=["lineas"])


@router.get("/", response_model=list[schemas.LineaProduccionOut])
def list_lineas(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    return db.query(models.LineaProduccion).filter(models.LineaProduccion.activo == True).all()
