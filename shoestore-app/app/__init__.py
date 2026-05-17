from flask import Flask

from .extensions import appbuilder, db


def create_app():
    app = Flask(__name__)

    app.config.from_object("config")

    db.init_app(app)

    with app.app_context():

        # importar modelos
        from . import models

        db.create_all()

        # inicializar AppBuilder
        appbuilder.init_app(app, db.session)

        # importar vistas normales (FAB)
        from . import views

        # 🔥 IMPORTANTE: registrar POS (sistema de ventas real)

    return app