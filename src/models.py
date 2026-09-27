from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional

class SolicitudPoliza(BaseModel):
    numero_poliza: str
    titular: str
    tipo_documento: str
    documento_identidad: str
    email_titular: str
    telefono_titular: str
    direccion: str
    ciudad: str
    ramo: str
    tipo_cobertura: str
    monto_asegurado: float
    prima_mensual: float
    deducible: float
    fecha_inicio_vigencia: str
    fecha_fin_vigencia: str
    frecuencia_pago:str
    metodo_pago: str
    agente_codigo: str
    agente_nombre: str
    beneficiarios: str
