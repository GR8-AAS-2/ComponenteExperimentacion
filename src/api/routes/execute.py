from flask import Blueprint, request, jsonify, render_template
from typing import Dict, Any
import asyncio
import os
import json
import random

from src.models import SolicitudPoliza

from src.services import generar_token_motorpolizas, generar_solicitudes_polizas, MotorPolizasService, RespuestaIncidentesService
from src.db import db

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../templates'))
execute_bp = Blueprint("execute", __name__, url_prefix="/api/v1", template_folder=template_dir)

@execute_bp.route("/execute", methods=["POST"])
def execute_consenso():
    
    try:
        datos = request.get_json()
        
        if not datos:
            return jsonify({
                "error": "El body de la petición no puede estar vacío",
                "codigo": 400
            }), 400

        cantidad_polizas = datos.get("cantidad_polizas", 10)
        cantidad_modificar = datos.get("cantidad_modificar", 5)
        ip_habitual = datos.get("ip_habitual", "192.0.2.10")
        ip_nueva = datos.get("ip_nueva", "198.51.100.45")
        usuario_id = datos.get("usuario_id", "USR_DEV_01")
        
        solicitudes = generar_solicitudes_polizas(cantidad_polizas)

        servicioMotorPolizas = MotorPolizasService()
        #servicioRespuestaIncidentes = RespuestaIncidentesService()

        respuestasPolizas = asyncio.run(
            servicioMotorPolizas.process_solicitudesPolizas(solicitudes)
        )

        ids_polizas = [
            res["poliza"]["id"] 
            for res in respuestasPolizas 
            if "poliza" in res and "id" in res["poliza"]
        ]

        print("Se obtuvieron los siguientes IDs de pólizas:", ids_polizas)

        cantidad_a_tomar = min(cantidad_modificar, len(ids_polizas))
        ids_a_modificar = random.sample(ids_polizas, cantidad_a_tomar)

        print(f"IDs seleccionados al azar ({len(ids_a_modificar)}): {ids_a_modificar}")

        filas_actualizadas = db.actualizar_documentos_por_lista_ids(ids_a_modificar)
        print(f"Se actualizaron exitosamente {filas_actualizadas} pólizas en la base de datos.")

        print(f"IDs extraídos para consultar: {ids_polizas}")
        consultas_get = asyncio.run(
            servicioMotorPolizas.process_get_polizas_by_ids(ids_polizas)
        )

        rol_anterior = "ADMIN"
        rol_nuevo = "SUPERADMIN"
        elevacion_privilegios = asyncio.run(
                    servicioMotorPolizas.send_post_elevacion_privilegios(
                        usuario_id=usuario_id,
                        rol_anterior=rol_anterior,
                        rol_nuevo=rol_nuevo,
                        ip_origen=ip_habitual
                    )
                )
        elevacion_privilegios = asyncio.run(
                    servicioMotorPolizas.send_post_elevacion_privilegios(
                        usuario_id=usuario_id,
                        rol_anterior=rol_anterior,
                        rol_nuevo=rol_nuevo,
                        ip_origen=ip_habitual
                    )
                )

        #192.0.2.10
        #198.51.100.45
        print("Se intentará realizar elevación de privilegios para el usuario " + usuario_id + " con rol " + rol_anterior + " a rol " + rol_nuevo + ", desde IP " + ip_nueva)
        elevacion_privilegios = asyncio.run(
            servicioMotorPolizas.send_post_elevacion_privilegios(
                usuario_id=usuario_id,
                rol_anterior=rol_anterior,
                rol_nuevo=rol_nuevo,
                ip_origen=ip_nueva
            )
        )

        print("Resultado de la elevación de privilegios:", elevacion_privilegios)

        #print("Se consultará el estado de la elevación de privilegios para el usuario 'USR_DEV_01'")
        #estado_elevacion = asyncio.run(
        #    servicioRespuestaIncidentes.get_elevacion_privilegios(
        #        usuario_id=usuario_id
        #    )
        #)

        #print(estado_elevacion)
        
        return consultas_get, 200, {'Content-Type': 'application/json'}
        
    except ValueError as e:
        print(e)
        return jsonify({
            "error": f"Error de validación: {str(e)}",
            "codigo": 400
        }), 400
    except Exception as e:
        print(e)
        return jsonify({
            "error": f"Error interno del servidor: {str(e)}",
            "codigo": 500
        }), 500


@execute_bp.route("/health", methods=["GET"])
def health_check():
    """Verificar estado del servicio"""
    return jsonify({
        "status": "ok",
        "message": "Servicio de consenso activo"
    }), 200
