from flask_appbuilder import ModelView, BaseView, expose
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask import render_template, request, redirect, url_for
from datetime import date

from .extensions import appbuilder, db
from .models import (Categoria, Producto, Cliente, Venta, DetalleVenta,
)

class CategoriaView(ModelView):
    datamodel = SQLAInterface(Categoria)
    list_columns = ["id", "nombre"]


class ProductoView(ModelView):
    datamodel = SQLAInterface(Producto)
    list_columns = ["id", "nombre", "precio", "stock", "categoria"]


class ClienteView(ModelView):
    datamodel = SQLAInterface(Cliente)
    list_columns = ["id", "nombre", "telefono", "correo"]


class VentaView(ModelView):
    datamodel = SQLAInterface(Venta)
    list_columns = ["id", "fecha", "cliente", "total"]


class DetalleVentaView(ModelView):
    datamodel = SQLAInterface(DetalleVenta)
    list_columns = ["id", "venta", "producto", "cantidad", "subtotal"]


# =========================
# POS INTEGRADO CORRECTO
# =========================

class POSView(BaseView):
    default_view = "index"

    @expose("/")
    def index(self):

        productos = db.session.query(Producto).all()
        clientes = db.session.query(Cliente).all()

        return self.render_template(
            "pos.html",
            productos=productos,
            clientes=clientes
        )

    @expose("/save", methods=["POST"])
    def save(self):

        cliente_id = request.form.get("cliente")
        productos_ids = request.form.getlist("producto_id")
        cantidades = request.form.getlist("cantidad")

        total = 0

        venta = Venta(
            fecha=date.today(),
            cliente_id=cliente_id,
            total=0
        )

        db.session.add(venta)
        db.session.commit()

        for i in range(len(productos_ids)):

            producto = db.session.get(Producto, int(productos_ids[i]))
            cantidad = int(cantidades[i])

            if producto.stock < cantidad:
                continue

            subtotal = producto.precio * cantidad
            total += subtotal

            producto.stock -= cantidad

            detalle = DetalleVenta(
                venta_id=venta.id,
                producto_id=producto.id,
                cantidad=cantidad,
                subtotal=subtotal
            )

            db.session.add(detalle)

        venta.total = total
        db.session.commit()

        # ✔ IMPORTANTE: volver al mismo módulo sin salir del sistema
        return redirect(url_for("POSView.index"))


# =========================
# REGISTER VIEWS
# =========================

appbuilder.add_view(
    CategoriaView,
    "Categorias",
    icon="fa-folder-open",
    category="Inventario",
)

appbuilder.add_view(
    ProductoView,
    "Productos",
    icon="fa-shopping-cart",
    category="Inventario",
)

appbuilder.add_view(
    ClienteView,
    "Clientes",
    icon="fa-users",
    category="Ventas",
)

appbuilder.add_view(
    VentaView,
    "Ventas",
    icon="fa-money",
    category="Ventas",
)

appbuilder.add_view(
    DetalleVentaView,
    "Detalle Ventas",
    icon="fa-list",
    category="Ventas",
)

# =========================
# POS (CORRECTO EN MENÚ)
# =========================

appbuilder.add_view(
    POSView,
    "Nueva Venta",
    icon="fa-shopping-cart",
    category="Ventas",
)