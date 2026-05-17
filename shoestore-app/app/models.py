from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import date


class Categoria(Model):
    __tablename__ = "categoria"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)

    productos = relationship("Producto", back_populates="categoria")

    def __repr__(self):
        return self.nombre


class Producto(Model):
    __tablename__ = "producto"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    precio = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)

    categoria_id = Column(Integer, ForeignKey("categoria.id"))
    categoria = relationship("Categoria", back_populates="productos")

    detalles = relationship("DetalleVenta", back_populates="producto")

    def __repr__(self):
        return self.nombre


class Cliente(Model):
    __tablename__ = "cliente"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    telefono = Column(String(20))
    correo = Column(String(100))

    ventas = relationship("Venta", back_populates="cliente")

    def __repr__(self):
        return self.nombre


class Venta(Model):
    __tablename__ = "venta"

    id = Column(Integer, primary_key=True)
    fecha = Column(Date, default=date.today)
    total = Column(Float, nullable=False)

    cliente_id = Column(Integer, ForeignKey("cliente.id"))
    cliente = relationship("Cliente", back_populates="ventas")

    detalles = relationship("DetalleVenta", back_populates="venta")

    def __repr__(self):
        return f"Venta {self.id}"


class DetalleVenta(Model):
    __tablename__ = "detalle_venta"

    id = Column(Integer, primary_key=True)

    venta_id = Column(Integer, ForeignKey("venta.id"))
    producto_id = Column(Integer, ForeignKey("producto.id"))

    cantidad = Column(Integer, nullable=False)
    subtotal = Column(Float, nullable=False)

    venta = relationship("Venta", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalles")