"""Configuración de variables de entorno y constantes del sistema."""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class DatabaseConfig(BaseSettings):
    """Configuración de conexiones a bases de datos."""
    
    # Conexión 67 (espejo de 36)
    db_67_host: str
    db_67_port: int
    db_67_name: str
    db_67_user: str
    db_67_pass: str
    
    # Conexión 38
    db_38_host: str
    db_38_port: int
    db_38_name: str
    db_38_user: str
    db_38_pass: str
    
    # Conexión 39
    db_39_host: str
    db_39_port: int
    db_39_name: str
    db_39_user: str
    db_39_pass: str
    
    # Conexión 82
    db_82_host: str
    db_82_port: int
    db_82_name: str
    db_82_user: str
    db_82_pass: str
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",
    }

class PoolSettings(BaseSettings):
    """Configuración optimizada de pools de conexiones por BD."""
    
    # ========== CONEXIÓN 36/67 - MySQL Principal (2013-presente) ==========
    # Uso: ALTO - Datos actuales + históricos recientes
    conn_67_pool_size: int = 15
    conn_67_max_overflow: int = 25
    
    # ========== CONEXIÓN 38 - PostgreSQL Histórica (solo 2020) ==========
    # Uso: BAJO - Solo un año específico, consultas ocasionales
    conn_38_pool_size: int = 5
    conn_38_max_overflow: int = 10
    
    # ========== CONEXIÓN 39 - MySQL Histórica (2013-2020) ==========
    # Uso: MEDIO - Datos históricos, consultas frecuentes pero no críticas
    conn_39_pool_size: int = 10
    conn_39_max_overflow: int = 15
    
    # ========== CONEXIÓN 82 - MySQL Nueva Normativa (2025+) ==========
    # Uso: ALTO - Datos nuevos, alto uso esperado conforme crece
    conn_82_pool_size: int = 12
    conn_82_max_overflow: int = 20
    
    # ========== CONFIGURACIÓN COMÚN ==========
    pool_timeout: int = 30          # Tiempo máximo espera si pool lleno (segundos)
    pool_recycle: int = 3600         # Reciclar conexiones cada hora (evita stale connections)
    pool_pre_ping: bool = True       # Verificar conexión antes de usar
    echo_pool: bool = True           # True en desarrollo, False en producción
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",
    }

class AppConfig(BaseSettings):
    """Configuración general de la aplicación."""
    
    app_debug: bool = True
    app_port: int = 8050
    output_dir: str = "outputs"  # ← AGREGADO: Directorio por defecto
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",
    }
    
    def get_output_dir(self) -> Path:
        """
        Retorna directorio de outputs como Path, creándolo si no existe.
        
        Maneja tanto rutas relativas como absolutas.
        Si la ruta no puede crearse, usa fallback local.
        """
        try:
            output_path = Path(self.output_dir)
            
            # Si es ruta relativa, hacerla relativa al directorio actual
            if not output_path.is_absolute():
                output_path = Path.cwd() / output_path
            
            # Crear directorio si no existe
            output_path.mkdir(parents=True, exist_ok=True)
            
            return output_path
            
        except Exception as e:
            # Fallback: usar directorio local
            fallback_path = Path.cwd() / 'outputs'
            fallback_path.mkdir(parents=True, exist_ok=True)
            return fallback_path


# ==================== CONSTANTES DEL SISTEMA ====================

# Límites de registros (sistema progresivo)
FAST_QUERY_THRESHOLD = 100_000      # Consulta rápida sin advertencias
MEDIUM_QUERY_THRESHOLD = 500_000    # Consulta media con advertencia
LARGE_QUERY_THRESHOLD = 750_000     # Consulta grande requiere confirmación
MAX_RECORDS = 750_000                # Límite absoluto

# Límites de tiempo
FAST_QUERY_TIMEOUT = 60              # 1 minuto para consultas rápidas
MEDIUM_QUERY_TIMEOUT = 180           # 3 minutos para consultas medias
LARGE_QUERY_TIMEOUT = 300            # 5 minutos para consultas grandes

# Límites de rango de fechas
MAX_DATE_RANGE_YEARS = 3             # 3 años máximo
MAX_DATE_RANGE_DAYS = MAX_DATE_RANGE_YEARS * 365

# Límites de valores en filtros
MAX_MANUAL_VALUES = 100
MAX_LIST_VALUES = 1_000

# Límites de archivos
MAX_FILE_SIZE_MB = 100

# ==================== INSTANCIAS GLOBALES ====================

db_config = DatabaseConfig()
app_config = AppConfig()
pool_config = PoolSettings()