"""Inicialización del módulo API"""
from src.api.routes.execute import execute_bp


def register_blueprints(app):
    """Registra todos los blueprints en la aplicación Flask"""
    app.register_blueprint(execute_bp)
