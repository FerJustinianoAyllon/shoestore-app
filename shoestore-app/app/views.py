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
from .ia_service import generar_analisis

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

class Reporte1View(BaseView):
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
        
        labels = [p[0] for p in productos_vendidos]
        valores = [p[1] for p in productos_vendidos]
        
         # IA
        prompt = f"""
        Analiza estas estadísticas de una tienda de zapatos:

        Productos registrados: {total_productos}
        Clientes registrados: {total_clientes}
        Ventas realizadas: {total_ventas}
        Ingresos: {ingresos}

        Productos vendidos:
        {productos_vendidos}

        Genera un análisis corto y profesional.
        """

        analisis_ia = generar_analisis(prompt)

        return self.render_template(
            "reportes/reporte1.html",
            total_productos=total_productos,
            total_clientes=total_clientes,
            total_ventas=total_ventas,
            ingresos=ingresos,
            productos_vendidos=productos_vendidos,
            labels=labels,
            valores=valores,
            analisis_ia=analisis_ia
        )  
        
class Reporte2View(BaseView):
    default_view = "index"

    @expose("/")
    def index(self):

        total_productos = db.session.query(func.count(Producto.id)).scalar()

        total_clientes = db.session.query(func.count(Cliente.id)).scalar()

        total_ventas = db.session.query(func.count(Venta.id)).scalar()

        ingresos = db.session.query(func.sum(Venta.total)).scalar() or 0

        ventas_por_dia = (
            db.session.query(
                Venta.fecha,
                func.sum(Venta.total).label("total")
            )
            .group_by(Venta.fecha)
            .order_by(Venta.fecha)
            .all()
        )

        labels = [str(v[0]) for v in ventas_por_dia]

        valores = [float(v[1]) for v in ventas_por_dia]

        promedio_ventas = round(
            ingresos / total_ventas, 2
        ) if total_ventas > 0 else 0

        max_venta = max(valores) if valores else 0

        min_venta = min(valores) if valores else 0

        crecimiento = "Crecimiento estable"

        if len(valores) >= 2:
            if valores[-1] > valores[0]:
                crecimiento = "Las ventas muestran crecimiento"
            else:
                crecimiento = "Las ventas muestran disminución"

        # IA
        prompt = f"""
        Analiza las tendencias de ventas de una tienda de zapatos.

        Ventas por día:
        {ventas_por_dia}

        Promedio de ventas:
        {promedio_ventas}

        Venta máxima:
        {max_venta}

        Venta mínima:
        {min_venta}

        Genera:
        - análisis de comportamiento
        - patrones detectados
        - recomendaciones
        - posibles riesgos
        - sugerencias para aumentar ventas
        """

        analisis_ia = generar_analisis(prompt)

        return self.render_template(
            "reportes/reporte2.html",
            total_productos=total_productos,
            total_clientes=total_clientes,
            total_ventas=total_ventas,
            ingresos=ingresos,
            labels=labels,
            valores=valores,
            promedio_ventas=promedio_ventas,
            max_venta=max_venta,
            min_venta=min_venta,
            crecimiento=crecimiento,
            analisis_ia=analisis_ia
        )   
        
class Reporte3View(BaseView):
    default_view = "index"

    @expose("/")
    def index(self):

        total_productos = db.session.query(func.count(Producto.id)).scalar()

        total_clientes = db.session.query(func.count(Cliente.id)).scalar()

        total_ventas = db.session.query(func.count(Venta.id)).scalar()

        ingresos = db.session.query(func.sum(Venta.total)).scalar() or 0

        top_productos = (
            db.session.query(
                Producto.nombre,
                Producto.stock,
                func.sum(DetalleVenta.cantidad).label("cantidad")
            )
            .join(DetalleVenta)
            .group_by(Producto.nombre, Producto.stock)
            .order_by(func.sum(DetalleVenta.cantidad).desc())
            .limit(5)
            .all()
        )

        labels = [p[0] for p in top_productos]

        valores = [int(p[2]) for p in top_productos]

        producto_top = labels[0] if labels else "Sin datos"

        stock_bajo = [
            p[0]
            for p in top_productos
            if p[1] < 5
        ]

        recomendacion_stock = (
            "Se recomienda reabastecer productos con bajo stock."
            if stock_bajo else
            "El stock actual es estable."
        )

        # IA
        prompt = f"""
        Analiza estos productos más vendidos de una tienda de zapatos:

        {top_productos}

        Genera:
        - predicción de demanda
        - recomendaciones de negocio
        - productos prioritarios
        - riesgos de stock
        - sugerencias para aumentar ingresos
        - estrategias de ventas
        """

        analisis_ia = generar_analisis(prompt)

        return self.render_template(
            "reportes/reporte3.html",
            total_productos=total_productos,
            total_clientes=total_clientes,
            total_ventas=total_ventas,
            ingresos=ingresos,
            labels=labels,
            valores=valores,
            producto_top=producto_top,
            stock_bajo=stock_bajo,
            recomendacion_stock=recomendacion_stock,
            analisis_ia=analisis_ia,
            top_productos=top_productos
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
    Reporte1View,
    "Reporte General",
    icon="fa-bar-chart",
    category="IA Reportes",
)

appbuilder.add_view(
    Reporte2View,
    "Tendencias",
    icon="fa-line-chart",
    category="IA Reportes",
)

appbuilder.add_view(
    Reporte3View,
    "Predicción IA",
    icon="fa-brain",
    category="IA Reportes",
)