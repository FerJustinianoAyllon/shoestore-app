from flask_appbuilder import BaseView, expose
from flask import request, redirect, url_for
from datetime import date

from .extensions import appbuilder, db
from .models import Producto, Cliente, Venta, DetalleVenta


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

        return redirect(self.url_for("POSView.index"))