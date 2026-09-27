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

class RespuestaIncidentesService:
    
    def __init__(self):
        self.timeout = 30  # segundos
        self.url_respuestaincidentes = os.environ.get(
            "RESPUESTAINCIDENTES_URL"
        )

    async def get_elevacion_privilegios(
            self, 
            usuario_id: str,
        ) -> Dict[str, Any]:
            
            headers = {
                "X-API-Key": os.environ.get("RESPUESTAINCIDENTES_API_KEY"),
                "Content-Type": "application/json"
            }

            payload = {
                "usuario_id": usuario_id,
                }

            endpoint = f"{self.url_respuestaincidentes}/api/incidentes/elevacion-privilegios"
    
            inicio = time.perf_counter()
            
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        endpoint,
                        json=payload,
                        headers=headers
                    )
    
                    fin = time.perf_counter()
                    tiempo_tardado_ms = round((fin - inicio) * 1000, 2)
                    response.raise_for_status()
                    data = response.json()
                    data["tiempo_tardado"] = tiempo_tardado_ms
    
                    return data
            except httpx.RequestError as e:
                print(f"Error al comunicarse con el motor de respuesta a incidentes: {e}")
                raise
            except httpx.HTTPStatusError as e:
                fin = time.perf_counter()
                tiempo_tardado_ms = round((fin - inicio) * 1000, 2)
                print(f"Error HTTP del motor respuesta a incidentes: {e.response.status_code} - {e.response.text}")
                try:
                    data = e.response.json()
                    data["tiempo_tardado"] = tiempo_tardado_ms
                    return data
                except Exception:
                    raise


class MotorPolizasService:
    
    def __init__(self):
        self.timeout = 30  # segundos
        self.url_motorpolizas = os.environ.get(
            "MOTORPOLIZAS_URL"
        )

    async def send_post_to_motorpolizas(
        self, 
        url_motorpolizas: str,
        solicitud: SolicitudPoliza,
        ruta: str
    ) -> Dict[str, Any]:
        
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

    async def send_post_elevacion_privilegios(
            self, 
            usuario_id: str,
            rol_anterior: str,
            rol_nuevo: str,
            ip_origen: str,
        ) -> Dict[str, Any]:
            
            token, _ = generar_token_motorpolizas()

            payload = {
                "usuario_id": usuario_id,
                "rol_anterior": rol_anterior,
                "rol_nuevo": rol_nuevo,
                "ip_origen": ip_origen
            }
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            endpoint = f"{self.url_motorpolizas}/api/incidentes/elevacion-privilegios"
    
            inicio = time.perf_counter()
            
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        endpoint,
                        json=payload,
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
    

def generar_token_motorpolizas(codigo_usuario="USR_DEV_01", rol="ADMIN", horas_exp=24):
    secret_key = os.environ.get("JWT_SECRET_KEY_MOTORPOLIZAS")
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

def generar_lista_ips(cantidad_total=10, cantidad_sospechosas=3, ip_habitual="192.0.2.10"):
    if cantidad_sospechosas >= cantidad_total:
        raise ValueError("La cantidad de sospechosas debe ser menor al total para garantizar una habitual al inicio.")

    ips_sospechosas = []
    while len(ips_sospechosas) < cantidad_sospechosas:
        ip_nueva = fake.ipv4_private()
        if ip_nueva != ip_habitual and ip_nueva not in ips_sospechosas:
            ips_sospechosas.append(ip_nueva)

    cantidad_habituales_restantes = (cantidad_total - cantidad_sospechosas) - 1
    ips_restantes = ips_sospechosas + ([ip_habitual] * cantidad_habituales_restantes)

    random.shuffle(ips_restantes)

    return [ip_habitual] + ips_restantes
    

def generar_metricas_y_graficas_polizas(polizas):
    def get_val(item, key, default=None):
        if isinstance(item, dict):
            return item.get(key, default)
        return getattr(item, key, default)

    coinciden_hash = 0
    no_coinciden_hash = 0
    indeterminados_hash = 0

    tiempos_todos = []
    tiempos_hash_true = []
    tiempos_hash_false = []

    for p in polizas:
        hash_ok = get_val(p, "hash_coincide")
        
        try:
            tiempo = float(get_val(p, "tiempo_tardado", 0.0))
        except (ValueError, TypeError):
            tiempo = 0.0

        tiempos_todos.append(tiempo)

        if hash_ok is True:
            coinciden_hash += 1
            tiempos_hash_true.append(tiempo)
        elif hash_ok is False:
            no_coinciden_hash += 1
            tiempos_hash_false.append(tiempo)
        else:
            indeterminados_hash += 1

    total_polizas = len(polizas)
    porcentaje_integros = round((coinciden_hash / total_polizas * 100), 2) if total_polizas > 0 else 0.0

    tabla_metricas = {
        "total_polizas": total_polizas,
        "coinciden_hash": coinciden_hash,
        "no_coinciden_hash": no_coinciden_hash,
        "indeterminados_hash": indeterminados_hash,
        "porcentaje_integros": porcentaje_integros
    }

    plt.style.use('seaborn-v0_8-whitegrid')

    def dibujar_histograma(ax, tiempos_list, titulo, color_barras, color_borde):
        if tiempos_list:
            min_t, max_t = min(tiempos_list), max(tiempos_list)
            bin_start = math.floor(min_t / 10.0) * 10
            bin_end = math.ceil(max_t / 10.0) * 10
            if bin_start == bin_end:
                bin_end += 10
            bins = np.arange(bin_start, bin_end + 10, 10)

            ax.hist(tiempos_list, bins=bins, color=color_barras, edgecolor=color_borde, alpha=0.7)
            
            p50 = np.percentile(tiempos_list, 50)
            p90 = np.percentile(tiempos_list, 90)
            p95 = np.percentile(tiempos_list, 95)

            ax.axvline(p50, color='#10B981', linestyle='--', linewidth=1.5, label=f'P50: {p50:.1f}ms')
            ax.axvline(p90, color='#F59E0B', linestyle='--', linewidth=1.5, label=f'P90: {p90:.1f}ms')
            ax.axvline(p95, color='#EF4444', linestyle='--', linewidth=1.5, label=f'P95: {p95:.1f}ms')
            
            ax.set_title(titulo, fontsize=10, fontweight='bold', pad=10)
            ax.set_xlabel("Latencia (ms)", fontsize=9)
            ax.set_ylabel("Frecuencia", fontsize=9)
            ax.legend(loc='upper right', fontsize=8)
            ax.yaxis.get_major_locator().set_params(integer=True)
        else:
            ax.text(0.5, 0.5, "Sin datos", ha='center', va='center')
            ax.set_title(titulo, fontsize=10, fontweight='bold', pad=10)

    fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    categorias = ["Hash Válido (True)", "Hash Alterado (False)"]
    valores = [coinciden_hash, no_coinciden_hash]
    colores = ['#10B981', '#EF4444']

    if indeterminados_hash > 0:
        categorias.append("Sin Estado")
        valores.append(indeterminados_hash)
        colores.append('#6B7280')

    bars1 = ax1.bar(categorias, valores, color=colores, width=0.4)
    ax1.set_title("Validación de Integridad (hash_coincide)", fontsize=11, fontweight='bold', pad=12)
    ax1.set_ylabel("Cantidad de Pólizas", fontsize=10)
    ax1.yaxis.get_major_locator().set_params(integer=True)

    for bar in bars1:
        h = bar.get_height()
        ax1.annotate(f'{h}', xy=(bar.get_x() + bar.get_width() / 2, h),
                     xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')

    ramos_str = [str(get_val(p, "ramo") or "N/A") for p in polizas]
    conteo_ramos = Counter(ramos_str)
    
    bars2 = ax2.bar(list(conteo_ramos.keys()), list(conteo_ramos.values()), color='#3B82F6', edgecolor='#1D4ED8', width=0.4)
    ax2.set_title("Pólizas Procesadas por Ramo", fontsize=11, fontweight='bold', pad=12)
    ax2.set_xlabel("Ramo", fontsize=10)
    ax2.set_ylabel("Cantidad", fontsize=10)
    ax2.yaxis.get_major_locator().set_params(integer=True)

    for bar in bars2:
        h = bar.get_height()
        ax2.annotate(f'{h}', xy=(bar.get_x() + bar.get_width() / 2, h),
                     xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    buffer1 = io.BytesIO()
    plt.savefig(buffer1, format='png', dpi=100)
    buffer1.seek(0)
    plt.close(fig1)

    grafico_b64_1 = f"data:image/png;base64,{base64.b64encode(buffer1.getvalue()).decode('utf-8')}"

    fig2, ax_gen = plt.subplots(figsize=(12, 4))
    dibujar_histograma(ax_gen, tiempos_todos, "Distribución General de Tiempos de Respuesta (Bins 10ms)", '#8B5CF6', '#6D28D9')
    
    plt.tight_layout()
    buffer2 = io.BytesIO()
    plt.savefig(buffer2, format='png', dpi=100)
    buffer2.seek(0)
    plt.close(fig2)

    grafico_b64_2 = f"data:image/png;base64,{base64.b64encode(buffer2.getvalue()).decode('utf-8')}"

    return tabla_metricas, grafico_b64_1, grafico_b64_2


def extraer_ip(item, llaves):
    if not isinstance(item, dict):
        return ""

    for key in llaves:
        valor = item.get(key)

        if valor is not None and str(valor).strip():
            return str(valor).strip()

    sub_obj = item.get("ultimo_cambio")

    if isinstance(sub_obj, dict):
        for key in llaves:
            valor = sub_obj.get(key)

            if valor is not None and str(valor).strip():
                return str(valor).strip()

    detalle = item.get("detalle")

    if isinstance(detalle, dict):
        for key in llaves:
            valor = detalle.get(key)

            if valor is not None and str(valor).strip():
                return str(valor).strip()

    return ""

def generar_metricas_y_graficas_eventos(eventos):

    habitual_ok = 0
    habitual_vuln = 0
    sospechosa_ok = 0
    sospechosa_vuln = 0

    tiempos_todos = []

    for i, e in enumerate(eventos):

        ip_habitual = str(
            e.get("ip_habitual", "")
        ).strip()

        ip_origen = str(
            e.get("ip_ultimo_cambio", "")
        ).strip()

        vulneracion = e.get(
            "vulneracion_detectada",
            False
        ) is True

        tiempo = e.get(
            "tiempo_tardado",
            0
        )

        try:
            tiempo = float(tiempo)
        except (ValueError, TypeError):
            tiempo = 0.0

        tiempos_todos.append(tiempo)

        es_habitual = (
            ip_habitual != ""
            and ip_origen != ""
            and ip_habitual == ip_origen
        )

        es_sospechosa = (
            ip_habitual != ""
            and ip_origen != ""
            and ip_habitual != ip_origen
        )

        if es_habitual and vulneracion:
            habitual_vuln += 1

        elif es_habitual and not vulneracion:
            habitual_ok += 1

        elif es_sospechosa and vulneracion:
            sospechosa_vuln += 1

        elif es_sospechosa and not vulneracion:
            sospechosa_ok += 1

    total_eventos = len(eventos)

    total_habituales = (
        habitual_ok +
        habitual_vuln
    )

    total_sospechosas = (
        sospechosa_ok +
        sospechosa_vuln
    )

    total_vulneraciones = (
        habitual_vuln +
        sospechosa_vuln
    )

    porcentaje_seguros = (
        round(
            (
                (habitual_ok + sospechosa_ok)
                / total_eventos
            ) * 100,
            2
        )
        if total_eventos
        else 0
    )

    tabla_metricas = {
        "total_eventos": total_eventos,
        "total_habituales": total_habituales,
        "total_sospechosas": total_sospechosas,
        "total_vulneraciones": total_vulneraciones,
        "habitual_sin_vulneracion": habitual_ok,
        "sospechosa_con_vulneracion": sospechosa_vuln,
        "porcentaje_seguros": porcentaje_seguros
    }

    plt.style.use("seaborn-v0_8-whitegrid")

    fig1, (ax1, ax2) = plt.subplots(
        1, 2,
        figsize=(12, 4.5)
    )

    categorias = [
        "IPs Habituales",
        "IPs Sospechosas"
    ]

    sin_vuln = [
        habitual_ok,
        sospechosa_ok
    ]

    con_vuln = [
        habitual_vuln,
        sospechosa_vuln
    ]

    x = np.arange(len(categorias))
    ancho = 0.35

    bars1_1 = ax1.bar(
        x - ancho / 2,
        sin_vuln,
        ancho,
        label="Sin Vulneración",
        color="#10B981"
    )

    bars1_2 = ax1.bar(
        x + ancho / 2,
        con_vuln,
        ancho,
        label="Vulneración Detectada",
        color="#EF4444"
    )

    ax1.set_title(
        f"Evaluación por Tipo de IP (Total: {total_eventos})",
        fontsize=11,
        fontweight="bold"
    )

    ax1.set_ylabel("Cantidad de Eventos")
    ax1.set_xticks(x)
    ax1.set_xticklabels(categorias)
    ax1.legend()

    ax1.yaxis.get_major_locator().set_params(integer=True)

    for bar in list(bars1_1) + list(bars1_2):
        h = bar.get_height()

        ax1.annotate(
            f"{int(h)}",
            xy=(
                bar.get_x() + bar.get_width() / 2,
                h
            ),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold"
        )

    estados_str = [
        str(
            e.get("estado", "desconocido")
            if isinstance(e, dict)
            else getattr(e, "estado", "desconocido")
        )
        for e in eventos
    ]

    conteo_estados = Counter(estados_str)

    bars2 = ax2.bar(
        list(conteo_estados.keys()),
        list(conteo_estados.values()),
        color="#3B82F6",
        edgecolor="#1D4ED8",
        width=0.4
    )

    ax2.set_title(
        "Distribución por Estado de Seguridad",
        fontsize=11,
        fontweight="bold"
    )

    ax2.set_xlabel("Estado")
    ax2.set_ylabel("Cantidad")

    ax2.yaxis.get_major_locator().set_params(integer=True)

    for bar in bars2:
        h = bar.get_height()

        ax2.annotate(
            f"{int(h)}",
            xy=(
                bar.get_x() + bar.get_width() / 2,
                h
            ),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9
        )

    plt.tight_layout()

    buffer1 = io.BytesIO()

    plt.savefig(
        buffer1,
        format="png",
        dpi=100,
        bbox_inches="tight"
    )

    buffer1.seek(0)
    plt.close(fig1)

    grafico_b64_1 = (
        "data:image/png;base64,"
        + base64.b64encode(
            buffer1.getvalue()
        ).decode("utf-8")
    )

    fig2, ax_gen = plt.subplots(
        figsize=(12, 4)
    )

    if tiempos_todos:

        min_t = min(tiempos_todos)
        max_t = max(tiempos_todos)

        bin_start = math.floor(min_t / 100.0) * 100
        bin_end = math.ceil(max_t / 100.0) * 100

        if bin_start == bin_end:
            bin_end += 100

        bins = np.arange(
            bin_start,
            bin_end + 100,
            100
        )

        ax_gen.hist(
            tiempos_todos,
            bins=bins,
            color="#8B5CF6",
            edgecolor="#6D28D9",
            alpha=0.7
        )

        p50 = np.percentile(tiempos_todos, 50)
        p90 = np.percentile(tiempos_todos, 90)
        p95 = np.percentile(tiempos_todos, 95)

        ax_gen.axvline(
            p50,
            color="#10B981",
            linestyle="--",
            linewidth=1.5,
            label=f"P50: {p50:.1f} ms"
        )

        ax_gen.axvline(
            p90,
            color="#F59E0B",
            linestyle="--",
            linewidth=1.5,
            label=f"P90: {p90:.1f} ms"
        )

        ax_gen.axvline(
            p95,
            color="#EF4444",
            linestyle="--",
            linewidth=1.5,
            label=f"P95: {p95:.1f} ms"
        )

        ax_gen.set_title(
            f"Distribución de Latencias "
            f"({len(tiempos_todos)} registros)",
            fontsize=10,
            fontweight="bold"
        )

        ax_gen.set_xlabel("Latencia (ms)")
        ax_gen.set_ylabel("Frecuencia")
        ax_gen.legend()

        ax_gen.yaxis.get_major_locator().set_params(
            integer=True
        )

    plt.tight_layout()

    buffer2 = io.BytesIO()

    plt.savefig(
        buffer2,
        format="png",
        dpi=100,
        bbox_inches="tight"
    )

    buffer2.seek(0)
    plt.close(fig2)

    grafico_b64_2 = (
        "data:image/png;base64,"
        + base64.b64encode(
            buffer2.getvalue()
        ).decode("utf-8")
    )

    return (
        tabla_metricas,
        grafico_b64_1,
        grafico_b64_2
    )
