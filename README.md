# Componente de experimentación

Este componente ejecuta un experimento de integridad de pólizas y seguridad de
eventos. Genera solicitudes de póliza de prueba, las envía al motor de pólizas,
consulta nuevamente las pólizas creadas, modifica aleatoriamente algunos
documentos en la base de datos para probar la integridad, y genera eventos de
elevación de privilegios desde una lista de direcciones IP. Finalmente, entrega
un reporte HTML con métricas, gráficas y los resultados detallados.

## Arquitectura

```
POST /api/v1/execute
		├── Leer parámetros del experimento y aplicar valores predeterminados
		├── Generar solicitudes de póliza sintéticas con Faker
		├── Para cada solicitud:
		│   ├── Generar un token JWT
		│   └── Enviar POST al motor: /api/polizas
		├── Seleccionar pólizas y modificar su documento_identidad en PostgreSQL
		├── Consultar cada póliza por ID: GET /api/polizas/{id}
		├── Generar IPs habituales y sospechosas
		├── Enviar eventos de elevación de privilegios al motor
		├── Calcular métricas y generar gráficas
		└── Renderizar y retornar src/templates/reporte.html
```

El componente está construido con Flask. `app.py` crea la aplicación para
ejecución local y `api/index.py` expone la misma aplicación como función para
Vercel. Las llamadas HTTP al motor se realizan con `httpx` y la base de datos
PostgreSQL se conecta mediante `psycopg2`.

## Instalación

### Requisitos

- Python 3.8 o superior.
- PostgreSQL accesible desde la aplicación.
- Un motor de pólizas compatible con los endpoints `/api/polizas` y
	`/api/incidentes/elevacion-privilegios`.
- Una tabla `polizas` con, al menos, las columnas `id` y
	`documento_identidad`.

### Pasos

1. Clonar o descargar el repositorio y entrar en su directorio:

```bash
cd ComponenteExperimentacion
```

2. Crear y activar un entorno virtual:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

3. Instalar las dependencias:

```bash
pip install -r requirements.txt
```

4. Crear un archivo `.env` con la configuración indicada en la siguiente
	 sección.

## Configuración

La aplicación carga automáticamente las variables definidas en `.env`.

```dotenv
DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/base_datos
MOTORPOLIZAS_URL=http://localhost:8001
JWT_SECRET_KEY_MOTORPOLIZAS=llave-secreta-jwt
JWT_ALGORITHM=HS256
PORT=5000
DEBUG=False
```

Variables:

| Variable | Obligatoria | Descripción |
| --- | --- | --- |
| `DATABASE_URL` | Sí | Cadena de conexión de PostgreSQL. |
| `MOTORPOLIZAS_URL` | Sí | URL base del motor de pólizas. |
| `JWT_SECRET_KEY_MOTORPOLIZAS` | Sí | Clave para firmar los tokens enviados al motor. |
| `JWT_ALGORITHM` | No | Algoritmo JWT; por defecto `HS256`. |
| `PORT` | No | Puerto local; por defecto `5000`. |
| `DEBUG` | No | Activa el modo debug cuando vale `True`; por defecto `False`. |

El módulo de servicios también reconoce `RESPUESTAINCIDENTES_URL` y
`RESPUESTAINCIDENTES_API_KEY` para su servicio auxiliar de incidentes. El flujo
actual de `/execute` envía directamente los eventos al
`MOTORPOLIZAS_URL` configurado.

## Ejecución

```bash
python app.py
```

## Petición POST

### Endpoint

```http
POST http://localhost:5000/api/v1/execute
Content-Type: application/json
```

El body no puede estar vacío. Todos los campos son opcionales; si no se envían,
se usan estos valores:

| Campo | Tipo | Predeterminado | Descripción |
| --- | --- | --- | --- |
| `cantidad_polizas` | entero | `10` | Número de solicitudes de póliza que se generan. |
| `cantidad_modificar` | entero | `3` | Número máximo de pólizas cuyos documentos se modifican en PostgreSQL. |
| `ip_habitual` | cadena | `192.0.2.10` | IP considerada habitual. |
| `cantidad_ip_total` | entero | `10` | Cantidad total de eventos de elevación de privilegios. |
| `cantidad_ip_sospechosa` | entero | `3` | Cantidad de IPs sospechosas. Debe ser menor que `cantidad_ip_total`. |
| `usuario_id` | cadena | `USR_DEV_01` | Usuario utilizado en los eventos de elevación. |

Ejemplo:

```json
{
	"cantidad_polizas": 10,
	"cantidad_modificar": 3,
	"ip_habitual": "192.0.2.10",
	"cantidad_ip_total": 10,
	"cantidad_ip_sospechosa": 3,
	"usuario_id": "USR_DEV_01"
}
```

### Respuesta exitosa

La respuesta tiene `Content-Type: text/html; charset=utf-8` y contiene el
reporte generado con:

- métricas de integridad de hashes y tiempos de consulta de pólizas;
- métricas de IPs habituales, sospechosas y vulneraciones;
- cuatro gráficas incrustadas como imágenes Base64;
- detalle de las pólizas procesadas;
- un JSON incrustado en el elemento HTML `datos-respuesta` con las respuestas de
	las consultas `GET /api/polizas/{id}`;
- un JSON incrustado en `datos-elevacionprivilegios` con las respuestas de los
	eventos de elevación de privilegios.

### Errores

Body vacío:

```json
{
	"error": "El body de la petición no puede estar vacío",
	"codigo": 400
}
```

Los errores de validación responden con estado `400`. Los errores no controlados
responden con estado `500` y un objeto JSON con las claves `error` y `codigo`.

## Despliegue en Vercel

El archivo `vercel.json` configura `api/index.py` como función Python y dirige
las peticiones hacia esa función. Para desplegar, configura en Vercel las mismas
variables de entorno del archivo `.env`, especialmente `DATABASE_URL`,
`MOTORPOLIZAS_URL` y `JWT_SECRET_KEY_MOTORPOLIZAS`.
