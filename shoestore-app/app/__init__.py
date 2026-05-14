from flask import Flask

#from flask_appbuilder.extensions import db
from .extensions import appbuilder, db


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object("config")
    
    db.init_app(app)
    with app.app_context():
        #from .models import Marca, Calzado, Cliente, Pedido, DetallePedido
        db.create_all()
        appbuilder.init_app(app, db.session)
        from . import views
        # Registering the views and APIs
        ...
    return app
