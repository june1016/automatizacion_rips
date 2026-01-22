"""Configuración de conexiones a bases de datos con pools optimizados."""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from config.settings import db_config, pool_config

logger = logging.getLogger(__name__)


class DatabaseConnections:
    """Gestor de conexiones a bases de datos con pools optimizados por uso."""
    
    def __init__(self):
        self.engines = {}
        self.sessions = {}
        self._setup_connections()
        self._log_pool_configuration()
    
    def _setup_connections(self):
        """Configura las 4 conexiones con pools optimizados según patrón de uso."""
        
        # ========== CONEXIÓN 67 - MySQL Principal (2013-presente) ==========
        # Uso ALTO: Datos actuales + consultas frecuentes
        self.engines['67'] = create_engine(
            f"mysql+pymysql://{db_config.db_67_user}:{db_config.db_67_pass}"
            f"@{db_config.db_67_host}:{db_config.db_67_port}/{db_config.db_67_name}",
            poolclass=QueuePool,
            pool_size=pool_config.conn_67_pool_size,
            max_overflow=pool_config.conn_67_max_overflow,
            pool_timeout=pool_config.pool_timeout,
            pool_recycle=pool_config.pool_recycle,
            pool_pre_ping=pool_config.pool_pre_ping,
            echo_pool=pool_config.echo_pool
        )
        
        # ========== CONEXIÓN 38 - PostgreSQL Histórica (solo 2020) ==========
        # Uso BAJO: Solo un año, consultas ocasionales
        self.engines['38'] = create_engine(
            f"postgresql+psycopg2://{db_config.db_38_user}:{db_config.db_38_pass}"
            f"@{db_config.db_38_host}:{db_config.db_38_port}/{db_config.db_38_name}",
            poolclass=QueuePool,
            pool_size=pool_config.conn_38_pool_size,
            max_overflow=pool_config.conn_38_max_overflow,
            pool_timeout=pool_config.pool_timeout,
            pool_recycle=pool_config.pool_recycle,
            pool_pre_ping=pool_config.pool_pre_ping,
            echo_pool=pool_config.echo_pool
        )
        
        # ========== CONEXIÓN 39 - MySQL Histórica (2013-2020) ==========
        # Uso MEDIO: Datos históricos, uso frecuente
        self.engines['39'] = create_engine(
            f"mysql+pymysql://{db_config.db_39_user}:{db_config.db_39_pass}"
            f"@{db_config.db_39_host}:{db_config.db_39_port}/{db_config.db_39_name}",
            poolclass=QueuePool,
            pool_size=pool_config.conn_39_pool_size,
            max_overflow=pool_config.conn_39_max_overflow,
            pool_timeout=pool_config.pool_timeout,
            pool_recycle=pool_config.pool_recycle,
            pool_pre_ping=pool_config.pool_pre_ping,
            echo_pool=pool_config.echo_pool
        )
        
        # ========== CONEXIÓN 82 - MySQL Nueva Normativa (2025+) ==========
        # Uso ALTO: Datos nuevos, crecimiento esperado
        self.engines['82'] = create_engine(
            f"mysql+pymysql://{db_config.db_82_user}:{db_config.db_82_pass}"
            f"@{db_config.db_82_host}:{db_config.db_82_port}/{db_config.db_82_name}",
            poolclass=QueuePool,
            pool_size=pool_config.conn_82_pool_size,
            max_overflow=pool_config.conn_82_max_overflow,
            pool_timeout=pool_config.pool_timeout,
            pool_recycle=pool_config.pool_recycle,
            pool_pre_ping=pool_config.pool_pre_ping,
            echo_pool=pool_config.echo_pool
        )
        
        # Crear sesiones
        for conn_id, engine in self.engines.items():
            self.sessions[conn_id] = sessionmaker(bind=engine)
    
    def _log_pool_configuration(self):
        """Registra configuración de pools al inicializar."""
        logger.info("=" * 60)
        logger.info("CONFIGURACIÓN DE POOLS DE CONEXIONES")
        logger.info("=" * 60)
        
        for conn_id, engine in self.engines.items():
            pool = engine.pool
            logger.info(
                f"Conexión {conn_id}: "
                f"size={pool.size()} "
                f"max_overflow={pool._max_overflow} "
                f"timeout={pool._timeout}s "
                f"recycle={pool._recycle}s"
            )
        
        total_base = sum(
            engine.pool.size() for engine in self.engines.values()
        )
        total_max = sum(
            engine.pool.size() + engine.pool._max_overflow 
            for engine in self.engines.values()
        )
        
        logger.info("-" * 60)
        logger.info(f"Total base: {total_base} conexiones")
        logger.info(f"Total máximo: {total_max} conexiones")
        logger.info("=" * 60)
    
    def get_session(self, connection_id: str):
        """Obtiene una sesión para la conexión especificada."""
        if connection_id not in self.sessions:
            raise ValueError(f"Conexión {connection_id} no existe")
        return self.sessions[connection_id]()
    
    def get_pool_status(self, connection_id: str = None) -> dict:
        """
        Obtiene estado actual del pool de conexiones.
        
        Args:
            connection_id: ID específico o None para todas
            
        Returns:
            Dict con estadísticas del pool
        """
        if connection_id:
            if connection_id not in self.engines:
                raise ValueError(f"Conexión {connection_id} no existe")
            
            pool = self.engines[connection_id].pool
            return {
                'connection_id': connection_id,
                'size': pool.size(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'queue_size': pool._queue.qsize() if hasattr(pool, '_queue') else 0
            }
        
        # Retornar stats de todas las conexiones
        return {
            conn_id: self.get_pool_status(conn_id)
            for conn_id in self.engines.keys()
        }
    
    def close_all(self):
        """Cierra todas las conexiones y libera recursos."""
        logger.info("Cerrando todas las conexiones de pool...")
        for conn_id, engine in self.engines.items():
            engine.dispose()
            logger.info(f"Conexión {conn_id} cerrada")


# Instancia global
db_connections = DatabaseConnections()