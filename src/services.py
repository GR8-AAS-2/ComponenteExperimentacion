import httpx
import jwt
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
from collections import Counter
from src.models import SolicitudPoliza
import time
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import math
import numpy as np
from faker import Faker
import random

fake = Faker('es_CO')


class MotorPolizasService:
    
    def __init__(self):
        self.timeout = 30  # segundos
        self.url_motorpolizas = os.environ.get(
            "MOTORPOLIZAS_URL", 
            "https://componente-motor-polizas.vercel.app"
        )

    async def send_post_to_motorpolizas(
        self, 
        url_motorpolizas: str,
        solicitud: SolicitudPoliza,
        ruta: str
    ) -> Dict[str, Any]:
        
        # Corregido: desempaquetar la tupla (token, payload)
        token, _ = generar_token_motorpolizas()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        endpoint = f"{url_motorpolizas}{ruta}"

        inicio = time.perf_counter()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    endpoint,
                    json=solicitud.model_dump(),
                    headers=headers
                )

                fin = time.perf_counter()
                tiempo_tardado_ms = round((fin - inicio) * 1000, 2)
                response.raise_for_status()
                data = response.json()
                data["tiempo_tardado"] = tiempo_tardado_ms

                return data
        except httpx.RequestError as e:
            print(f"Error al comunicarse con el motor pólizas: {e}")
            raise
        except httpx.HTTPStatusError as e:
            fin = time.perf_counter()
            tiempo_tardado_ms = round((fin - inicio) * 1000, 2)
            print(f"Error HTTP del motor pólizas: {e.response.status_code} - {e.response.text}")
            try:
                data = e.response.json()
                data["tiempo_tardado"] = tiempo_tardado_ms
                return data
            except Exception:
                raise

    async def process_solicitudesPolizas(
        self, 
        solicitudes: List[SolicitudPoliza],
    ) -> List[Dict[str, Any]]:

        resultados = []
        print("Procesando solicitudes POST")
        for solicitud in solicitudes:
            inicio_individual = time.perf_counter()
            try:
                respuesta = await self.send_post_to_motorpolizas(
                    url_motorpolizas=self.url_motorpolizas,
                    solicitud=solicitud,
                    ruta="/api/polizas"
                )
                resultados.append(respuesta)
                                
            except Exception as e:
                fin_individual = time.perf_counter()
                tiempo_fallo_ms = round((fin_individual - inicio_individual) * 1000, 2)
                
                print(f"Error procesando solicitud: {e}")
                resultados.append({
                    "error": str(e),
                    "veredicto": "ERROR",
                    "tiempo_tardado": tiempo_fallo_ms
                })
        
        return resultados

    async def get_poliza_by_id(self, poliza_id: int) -> Dict[str, Any]:
        token, _ = generar_token_motorpolizas()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        endpoint = f"{self.url_motorpolizas}/api/polizas/{poliza_id}"

        inicio = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(endpoint, headers=headers)
                fin = time.perf_counter()
                tiempo_ms = round((fin - inicio) * 1000, 2)

                print(response)
                response.raise_for_status()
                data = response.json()
                if isinstance(data, dict):
                    data["tiempo_tardado"] = tiempo_ms
                return data

        except httpx.RequestError as e:
            print(f"Error de red al consultar póliza ID {poliza_id}: {e}")
            raise
        except httpx.HTTPStatusError as e:
            fin = time.perf_counter()
            tiempo_ms = round((fin - inicio) * 1000, 2)
            print(f"Error HTTP {e.response.status_code} para póliza ID {poliza_id}")
            try:
                data = e.response.json()
                data["tiempo_tardado"] = tiempo_ms
                return data
            except Exception:
                raise

    async def process_get_polizas_by_ids(self, poliza_ids: List[int]) -> List[Dict[str, Any]]:
        resultados = []
        print(f"Consultando {len(poliza_ids)} pólizas por ID...")

        for p_id in poliza_ids:
            inicio = time.perf_counter()
            try:
                respuesta = await self.get_poliza_by_id(p_id)
                resultados.append(respuesta)
            except Exception as e:
                fin = time.perf_counter()
                resultados.append({
                    "id_consultado": p_id,
                    "error": str(e),
                    "veredicto": "ERROR",
                    "tiempo_tardado": round((fin - inicio) * 1000, 2)
                })

        return resultados


def generar_token_motorpolizas(codigo_usuario="USR_DEV_01", rol="ADMIN", horas_exp=24):
    secret_key = os.environ.get("JWT_SECRET_KEY")
    algorithm = os.environ.get("JWT_ALGORITHM", "HS256")

    payload = {
        "codigo_usuario": codigo_usuario,
        "rol": rol,
        "exp": datetime.now(timezone.utc) + timedelta(hours=horas_exp),
        "iat": datetime.now(timezone.utc)
    }

    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    return token, payload


def generar_solicitudes_polizas(cantidad=10):
    solicitudes = []
    for _ in range(cantidad):
        nombre_titular = fake.name()
        fecha_inicio = fake.date_between(start_date="-1y", end_date="+1y")
        email_clean = nombre_titular.lower().replace(" ", ".")
        
        solicitud = SolicitudPoliza(
            numero_poliza=f"POL-{fake.year()}-AUT-{random.randint(1000, 9999)}",
            titular=nombre_titular,
            tipo_documento="CC",
            documento_identidad=str(fake.random_number(digits=10, fix_len=True)),
            email_titular=f"{email_clean}@email.com",
            telefono_titular=f"+57 {fake.msisdn()[3:]}",
            direccion=fake.street_address(),
            ciudad=fake.city(),
            ramo="Autos",
            tipo_cobertura="Todo riesgo Premium Gold",
            monto_asegurado=round(random.uniform(20_000_000, 200_000_000), 2),
            prima_mensual=round(random.uniform(100_000, 800_000), 2),
            deducible=round(random.uniform(500_000, 3_000_000), 2),
            fecha_inicio_vigencia=fecha_inicio.strftime("%Y-%m-%d"),
            fecha_fin_vigencia=(fecha_inicio + timedelta(days=365)).strftime("%Y-%m-%d"),
            frecuencia_pago="MENSUAL",
            metodo_pago="DEBITO_AUTOMATICO",
            agente_codigo=f"AGT-{random.randint(1, 99):02d}",
            agente_nombre=fake.name(),
            beneficiarios="Titular (100%)"
        )
        solicitudes.append(solicitud)

    return solicitudes