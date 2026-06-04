import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    rol = Column(String(20), nullable=False)  # solicitante | coordinador | bodeguero
    password_hash = Column(String(255), nullable=False)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Material(Base):
    __tablename__ = "materiales"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(30), unique=True, index=True, nullable=False)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    categoria = Column(String(20), nullable=False, default="produccion")  # produccion | epps | mantenimiento
    unidad_medida = Column(String(10), nullable=False)  # kg | unidad | litro
    precio_unitario = Column(Float, nullable=False)
    stock_actual = Column(Float, default=0.0)
    stock_minimo = Column(Float, default=0.0)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    alertas = relationship("Alerta", back_populates="material")
    detalles = relationship("DetalleSolicitud", back_populates="material")


class LineaProduccion(Base):
    __tablename__ = "lineas_produccion"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False, unique=True)
    descripcion = Column(Text)
    activo = Column(Boolean, default=True)

    solicitudes = relationship("Solicitud", back_populates="linea_produccion")


class Solicitud(Base):
    __tablename__ = "solicitudes"

    id = Column(Integer, primary_key=True, index=True)
    solicitante_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    linea_produccion_id = Column(Integer, ForeignKey("lineas_produccion.id"), nullable=False)
    estado = Column(String(20), default="pendiente")  # pendiente | aprobada | rechazada | entregada
    observaciones = Column(Text)
    fecha_requerida = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    solicitante = relationship("Usuario", foreign_keys=[solicitante_id])
    linea_produccion = relationship("LineaProduccion", back_populates="solicitudes")
    detalles = relationship("DetalleSolicitud", back_populates="solicitud", cascade="all, delete-orphan")
    historial = relationship("HistorialEstados", back_populates="solicitud", cascade="all, delete-orphan")


class DetalleSolicitud(Base):
    __tablename__ = "detalle_solicitud"

    id = Column(Integer, primary_key=True, index=True)
    solicitud_id = Column(Integer, ForeignKey("solicitudes.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materiales.id"), nullable=False)
    cantidad_solicitada = Column(Float, nullable=False)
    cantidad_aprobada = Column(Float, nullable=True)
    precio_unitario_snapshot = Column(Float, nullable=False)  # precio al momento de crear la solicitud

    solicitud = relationship("Solicitud", back_populates="detalles")
    material = relationship("Material", back_populates="detalles")

    @property
    def subtotal(self):
        qty = self.cantidad_aprobada if self.cantidad_aprobada is not None else self.cantidad_solicitada
        return round(qty * self.precio_unitario_snapshot, 2)


class HistorialEstados(Base):
    __tablename__ = "historial_estados"

    id = Column(Integer, primary_key=True, index=True)
    solicitud_id = Column(Integer, ForeignKey("solicitudes.id"), nullable=False)
    estado_anterior = Column(String(20))
    estado_nuevo = Column(String(20), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    comentario = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    solicitud = relationship("Solicitud", back_populates="historial")
    usuario = relationship("Usuario")


class Alerta(Base):
    __tablename__ = "alertas"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materiales.id"), nullable=False)
    tipo = Column(String(20), nullable=False)  # stock_bajo | sin_stock
    mensaje = Column(Text, nullable=False)
    activa = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    material = relationship("Material", back_populates="alertas")
