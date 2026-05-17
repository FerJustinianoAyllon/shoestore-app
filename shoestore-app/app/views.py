from flask_appbuilder import ModelView, BaseView, expose
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask import render_template, request, redirect, url_for
from datetime import date
from .extensions import appbuilder, db
from .models import (Categoria, Producto, Cliente, Venta, DetalleVenta)
from wtforms import FileField
from werkzeug.utils import secure_filename
import os
from flask import flash
from sqlalchemy import func

class CategoriaView(ModelView):
    datamodel = SQLAInterface(Categoria)
    list_columns = ["id", "nombre"]


class ProductoView(ModelView):
    datamodel = SQLAInterface(Producto)

    list_columns = [
        "id",
        "nombre",
        "precio",
        "stock",
        "imagen",
        "creado_en",
        "categoria"
    ]

    add_columns = [
        "nombre",
        "precio",
        "stock",
        "imagen",
        "categoria"
    ]

    edit_columns = [
        "nombre",
        "precio",
        "stock",
        "imagen",
        "categoria"
    ]

    add_form_extra_fields = {
        "imagen": FileField("Imagen")
    }

    edit_form_extra_fields = {
        "imagen": FileField("Imagen")
    }

    show_fieldsets = [
        ("Producto", {
            "fields": [
                "nombre",
                "precio",
                "stock",
                "imagen",
                "creado_en",
                "categoria"
            ]
        })
    ]

    def pre_add(self, item):

        file = request.files.get("imagen")

        if file and file.filename:

            filename = secure_filename(file.filename)

            upload_path = os.path.join(
                "app",
                "static",
                "uploads",
                filename
            )

            file.save(upload_path)

            item.imagen = filename

    def pre_update(self, item):

        file = request.files.get("imagen")

        if file and file.filename:

            filename = secure_filename(file.filename)

            upload_path = os.path.join(
                "app",
                "static",
                "uploads",
                filename
            )

            file.save(upload_path)

            item.imagen = filename


class ClienteView(ModelView):
    datamodel = SQLAInterface(Cliente)
    list_columns = ["id", "nombre", "telefono", "correo"]

class DetalleVentaView(ModelView):
    datamodel = SQLAInterface(DetalleVenta)
    list_columns = ["venta", "producto", "cantidad", "subtotal"]
    
    order_columns = ["venta", "producto","cantidad","subtotal"]
    
    search_columns = ["venta", "producto"]

    base_permissions = ["can_list", "can_show", "can_edit", "can_delete"]

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

#REPORTES

class ReporteView(BaseView):
    default_view = "index"

    @expose("/")
    def index(self):

        total_productos = db.session.query(func.count(Producto.id)).scalar()

        total_clientes = db.session.query(func.count(Cliente.id)).scalar()

        total_ventas = db.session.query(func.count(Venta.id)).scalar()

        ingresos = db.session.query(func.sum(Venta.total)).scalar() or 0

        productos_vendidos = (
            db.session.query(
                Producto.nombre,
                func.sum(DetalleVenta.cantidad).label("total")
            )
            .join(DetalleVenta)
            .group_by(Producto.nombre)
            .all()
        )

        return self.render_template(
            "reportes.html",
            total_productos=total_productos,
            total_clientes=total_clientes,
            total_ventas=total_ventas,
            ingresos=ingresos,
            productos_vendidos=productos_vendidos
        )      

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
    DetalleVentaView,
    "Detalle Ventas",
    icon="fa-list",
    category="Ventas",
)

appbuilder.add_view(
    POSView,
    "Nueva Venta",
    icon="fa-shopping-cart",
    category="Ventas",
)

appbuilder.add_view(
    ReporteView,
    "Reportes",
    icon="fa-bar-chart",
    category="Reportes",
)