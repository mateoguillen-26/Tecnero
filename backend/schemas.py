from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime


# ─── Auth ────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    rol: str
    nombre: str
    id: int


# ─── Usuarios ────────────────────────────────────────────────────────────────

class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    rol: str
    password: str

    @field_validator("rol")
    @classmethod
    def rol_valido(cls, v):
        if v not in ("solicitante", "coordinador", "bodeguero"):
            raise ValueError("Rol debe ser solicitante, coordinador o bodeguero")
        return v


class UsuarioOut(BaseModel):
    id: int
    nombre: str
    email: str
    rol: str
    activo: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Materiales ──────────────────────────────────────────────────────────────

class MaterialCreate(BaseModel):
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    categoria: str = "produccion"
    unidad_medida: str
    precio_unitario: float
    stock_actual: float = 0.0
    stock_minimo: float = 0.0

    @field_validator("unidad_medida")
    @classmethod
    def unidad_valida(cls, v):
        if v not in ("kg", "unidad", "litro"):
            raise ValueError("Unidad debe ser kg, unidad o litro")
        return v

    @field_validator("categoria")
    @classmethod
    def categoria_valida(cls, v):
        if v not in ("produccion", "epps", "mantenimiento"):
            raise ValueError("Categoria debe ser produccion, epps o mantenimiento")
        return v

    @field_validator("precio_unitario")
    @classmethod
    def precio_positivo(cls, v):
        if v <= 0:
            raise ValueError("El precio unitario debe ser mayor a 0")
        return v

    @field_validator("stock_actual", "stock_minimo")
    @classmethod
    def stock_no_negativo(cls, v):
        if v < 0:
            raise ValueError("El stock no puede ser negativo")
        return v


class MaterialUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    unidad_medida: Optional[str] = None
    precio_unitario: Optional[float] = None
    stock_actual: Optional[float] = None
    stock_minimo: Optional[float] = None
    activo: Optional[bool] = None


class MaterialOut(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: Optional[str]
    categoria: str
    unidad_medida: str
    precio_unitario: float
    stock_actual: float
    stock_minimo: float
    activo: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Líneas de producción ─────────────────────────────────────────────────────

class LineaProduccionOut(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    activo: bool

    model_config = {"from_attributes": True}


# ─── Solicitudes ─────────────────────────────────────────────────────────────

class DetalleSolicitudCreate(BaseModel):
    material_id: int
    cantidad_solicitada: float

    @field_validator("cantidad_solicitada")
    @classmethod
    def cantidad_positiva(cls, v):
        if v <= 0:
            raise ValueError("La cantidad debe ser mayor a 0")
        return v


class SolicitudCreate(BaseModel):
    linea_produccion_id: int
    fecha_requerida: datetime
    observaciones: Optional[str] = None
    items: List[DetalleSolicitudCreate]

    @field_validator("items")
    @classmethod
    def items_no_vacios(cls, v):
        if not v:
            raise ValueError("La solicitud debe tener al menos un ítem")
        return v


class DetalleOut(BaseModel):
    id: int
    material_id: int
    material_codigo: Optional[str]
    material_nombre: str
    material_unidad: str
    cantidad_solicitada: float
    cantidad_aprobada: Optional[float]
    precio_unitario_snapshot: float
    subtotal: float
    material_stock_actual: Optional[float] = None  # stock al momento de consultar

    model_config = {"from_attributes": True}


class SolicitudOut(BaseModel):
    id: int
    solicitante_id: int
    solicitante_nombre: str
    linea_produccion_id: int
    linea_produccion_nombre: str
    estado: str
    observaciones: Optional[str]
    fecha_requerida: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    detalles: List[DetalleOut]
    total: float

    model_config = {"from_attributes": True}


class SolicitudResumen(BaseModel):
    id: int
    solicitante_nombre: str
    linea_produccion_nombre: str
    estado: str
    fecha_requerida: Optional[datetime]
    created_at: datetime
    total: float
    num_items: int

    model_config = {"from_attributes": True}


# ─── Aprobación ──────────────────────────────────────────────────────────────

class ItemAprobacion(BaseModel):
    detalle_id: int
    cantidad_aprobada: float

    @field_validator("cantidad_aprobada")
    @classmethod
    def cantidad_no_negativa(cls, v):
        if v < 0:
            raise ValueError("La cantidad aprobada no puede ser negativa")
        return v


class AprobacionRequest(BaseModel):
    accion: str  # "aprobar" | "rechazar"
    comentario: Optional[str] = None
    items: Optional[List[ItemAprobacion]] = None  # solo en aprobación

    @field_validator("accion")
    @classmethod
    def accion_valida(cls, v):
        if v not in ("aprobar", "rechazar"):
            raise ValueError("Acción debe ser 'aprobar' o 'rechazar'")
        return v


# ─── Historial ───────────────────────────────────────────────────────────────

class HistorialOut(BaseModel):
    id: int
    estado_anterior: Optional[str]
    estado_nuevo: str
    usuario_nombre: str
    comentario: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Alertas ─────────────────────────────────────────────────────────────────

class AlertaOut(BaseModel):
    id: int
    material_id: int
    material_nombre: str
    tipo: str
    mensaje: str
    activa: bool
    created_at: datetime
    stock_actual: float
    stock_minimo: float

    model_config = {"from_attributes": True}


# ─── Dashboard ───────────────────────────────────────────────────────────────

class KPIOut(BaseModel):
    total_solicitudes_mes: int
    monto_total_mes: float
    solicitudes_pendientes: int
    alertas_activas: int


class GastoLineaItem(BaseModel):
    linea: str
    total: float
    porcentaje: float


class TopMaterialItem(BaseModel):
    material: str
    unidad: str
    total_valor: float
    total_cantidad: float


class StockItem(BaseModel):
    id: int
    nombre: str
    unidad_medida: str
    stock_actual: float
    stock_minimo: float
    estado: str  # normal | bajo | sin_stock
    precio_unitario: float


class DashboardOut(BaseModel):
    kpis: KPIOut
    gasto_por_linea: List[GastoLineaItem]
    top_materiales: List[TopMaterialItem]
    inventario: List[StockItem]
    alertas: List[AlertaOut]
