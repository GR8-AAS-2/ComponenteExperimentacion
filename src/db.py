import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List
from contextlib import contextmanager


class DatabaseConnection:
    
    def __init__(self):
        self.db_url = os.environ.get("DATABASE_URL")
    
    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = psycopg2.connect(self.db_url)
            yield conn
        except psycopg2.Error as e:
            print(f"Error de conexión a la base de datos: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def actualizar_documentos_por_lista_ids(self, poliza_ids: List[int]) -> int:
        if not poliza_ids:
            return 0

        query = """
            UPDATE polizas 
            SET documento_identidad = LPAD(FLOOR(RANDOM() * 10000000000)::BIGINT::TEXT, 10, '0')
            WHERE id = ANY(%s)
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (poliza_ids,))
                    conn.commit()
                    return cursor.rowcount
        except psycopg2.Error as e:
            print(f"Error al actualizar la lista de pólizas: {e}")
            raise

db = DatabaseConnection()
