from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()


def create_app():
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
    
    app = Flask(__name__, template_folder=template_dir)
    
    # Configuración CORS
    CORS(app)
    
    # Configuración de la aplicación
    app.config["JSON_SORT_KEYS"] = False
    
    # Registrar blueprint de salud
    @app.route("/")
    def health_check():
        return {
            "status": "ok", 
            "message": "Servicio de componente de experimentación activo",
            "version": "1.0.0"
        }
    
    # Registrar blueprints de API
    from src.api import register_blueprints
    register_blueprints(app)
    
    return app