import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user, require_roles
import models
import schemas

router = APIRouter(prefix="/api/materiales", tags=["materiales"])


def verificar_y_crear_alerta(db: Session, material: models.Material):
    """Verifica el stock del material y crea/actualiza alertas automáticamente."""
    if material.stock_actual <= 0:
        tipo = "sin_stock"
        mensaje = f"'{material.nombre}' sin stock (stock actual: {material.stock_actual} {material.unidad_medida})"
    elif material.stock_actual <= material.stock_minimo:
        tipo = "stock_bajo"
        mensaje = f"'{material.nombre}' con stock bajo (actual: {material.stock_actual}, mínimo: {material.stock_minimo} {material.unidad_medida})"
    else:
        # Stock normal: desactivar alertas activas de este material
        db.query(models.Alerta).filter(
            models.Alerta.material_id == material.id,
            models.Alerta.activa == True,
        ).update({"activa": False})
        db.commit()
        return

    # Buscar alerta activa existente del mismo tipo
    alerta_existente = db.query(models.Alerta).filter(
        models.Alerta.material_id == material.id,
        models.Alerta.activa == True,
    ).first()

    if alerta_existente:
        # Actualizar tipo y mensaje si cambió
        alerta_existente.tipo = tipo
        alerta_existente.mensaje = mensaje
    else:
        nueva_alerta = models.Alerta(
            material_id=material.id,
            tipo=tipo,
            mensaje=mensaje,
            activa=True,
        )
        db.add(nueva_alerta)
    db.commit()


@router.get("/", response_model=list[schemas.MaterialOut])
def list_materiales(
    solo_activos: bool = True,
    categoria: str = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    q = db.query(models.Material)
    if solo_activos:
        q = q.filter(models.Material.activo == True)
    if categoria:
        q = q.filter(models.Material.categoria == categoria)
    return q.order_by(models.Material.codigo).all()


@router.get("/{material_id}", response_model=schemas.MaterialOut)
def get_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    material = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material no encontrado")
    return material


@router.post("/", response_model=schemas.MaterialOut)
def create_material(
    data: schemas.MaterialCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_roles("coordinador", "bodeguero")),
):
    existing_codigo = db.query(models.Material).filter(models.Material.codigo == data.codigo).first()
    if existing_codigo:
        raise HTTPException(status_code=400, detail=f"Ya existe un material con el código {data.codigo}")

    material = models.Material(
        codigo=data.codigo,
        nombre=data.nombre,
        descripcion=data.descripcion,
        categoria=data.categoria,
        unidad_medida=data.unidad_medida,
        precio_unitario=data.precio_unitario,
        stock_actual=data.stock_actual,
        stock_minimo=data.stock_minimo,
    )
    db.add(material)
    db.commit()
    db.refresh(material)

    verificar_y_crear_alerta(db, material)
    db.refresh(material)
    return material


@router.put("/{material_id}", response_model=schemas.MaterialOut)
def update_material(
    material_id: int,
    data: schemas.MaterialUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_roles("coordinador", "bodeguero")),
):
    material = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material no encontrado")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(material, field, value)

    material.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(material)

    verificar_y_crear_alerta(db, material)
    db.refresh(material)
    return material


@router.delete("/{material_id}")
def delete_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_roles("coordinador")),
):
    material = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material no encontrado")

    # Soft delete
    material.activo = False
    material.updated_at = datetime.datetime.utcnow()
    db.commit()
    return {"detail": "Material desactivado correctamente"}
