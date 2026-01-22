"""Controller para operaciones de tipo RIPS AC."""
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from models.base import GlobalFilters, QueryResult
from models.ac_model import ACSpecificFilters, AC_EXPORT_COLUMNS
from services.query_builder import ACQueryBuilder
from services.data_processor import ACDataProcessor
from utils.validators import DateValidator, ValueValidator, RecordCountValidator, QueryWithoutFiltersValidator
from config.settings import MAX_RECORDS
from config.settings import app_config

logger = logging.getLogger(__name__)


@dataclass
class ACOperationResult:
    """Resultado de operación del controller."""
    success: bool
    message: str
    query_result: Optional[QueryResult] = None
    csv_filepath: Optional[str] = None
    error_details: Optional[str] = None


class ACController:
    """Controller para gestionar operaciones de consultas AC."""
    
    def __init__(self, normativa: str):
        """
        Args:
            normativa: '3374' o '2275'
        """
        if normativa not in ['3374', '2275']:
            raise ValueError(f"Normativa inválida: {normativa}")
        
        self.normativa = normativa
        self.query_builder = ACQueryBuilder(normativa)
        self.data_processor = ACDataProcessor(normativa)
    
    def execute_query(
        self,
        global_filters: GlobalFilters,
        specific_filters: ACSpecificFilters,
        columns: List[str],
    ) -> ACOperationResult:
        """
        Ejecuta consulta completa de AC con validaciones.
        
        Args:
            global_filters: Filtros globales (fecha obligatoria)
            specific_filters: Filtros específicos de AC
            columns: Lista de columnas a exportar
        
        Returns:
            ACOperationResult con resultado de la operación
        """
        logger.info(f"Iniciando ejecución de consulta AC - Normativa {self.normativa}")
        
        # Paso 1: Validar inputs
        validation_result = self._validate_inputs(
            global_filters,
            specific_filters,
            columns
        )
        
        if not validation_result.success:
            return validation_result
        
        # Paso 2: Determinar conexiones según rango de fechas
        connections = global_filters.date_range.get_connections()
        logger.info(f"Conexiones a consultar: {connections}")
        
        # Paso 3: Construir queries para cada conexión
        queries = {}
        for conn_id in connections:
            query, params = self.query_builder.build_query(
                connection_id=conn_id,
                global_filters=global_filters,
                specific_filters=specific_filters,
                columns=columns
            )
            queries[conn_id] = (query, params)
        
        # Paso 4: Estimación deshabilitada - validación solo post-ejecución
        logger.info("Estimación pre-ejecución deshabilitada")
        logger.info(f"Query se ejecutará directamente en conexiones: {connections}")
        logger.info("Validación de límites aplicará después de obtener resultados")
        
        # Paso 5: Ejecutar queries y consolidar
        try:
            query_result = self.data_processor.execute_and_consolidate(queries)
        except Exception as e:
            logger.error(f"Error durante ejecución: {str(e)}")
            return ACOperationResult(
                success=False,
                message="Error durante ejecución de consulta",
                error_details=str(e)
            )
        
        # Paso 6: Validar límites post-ejecución
        limit_check = RecordCountValidator.check_limit(query_result.record_count)
        
        if limit_check[0] == 'error':
            logger.warning(f"Límite excedido: {query_result.record_count} registros")
            return ACOperationResult(
                success=False,
                message=limit_check[1],
                query_result=query_result
            )
        
        # Paso 7: Exportar a CSV
        try:
            filename = self._generate_filename()
            csv_filepath = self.data_processor.export_to_csv(
                query_result=query_result,
                filename=filename,
                output_dir=app_config.get_output_dir()
            )
        except Exception as e:
            logger.error(f"Error durante exportación: {str(e)}")
            return ACOperationResult(
                success=False,
                message="Error durante exportación de CSV",
                query_result=query_result,
                error_details=str(e)
            )
        
        # Paso 8: Retornar resultado exitoso
        logger.info(f"Consulta completada exitosamente: {query_result.record_count} registros")
        
        success_message = (
            f"Consulta completada: {query_result.record_count:,} registros "
            f"en {query_result.execution_time:.2f}s"
        )
        
        if limit_check[0] == 'warning':
            success_message += f"\n⚠️ {limit_check[1]}"
        
        return ACOperationResult(
            success=True,
            message=success_message,
            query_result=query_result,
            csv_filepath=csv_filepath
        )
    
    def _validate_inputs(
        self,
        global_filters: GlobalFilters,
        specific_filters: ACSpecificFilters,
        columns: List[str]
    ) -> ACOperationResult:
        """Valida todos los inputs antes de ejecutar."""
        
        # Validación 1: Rango de fechas
        date_valid, date_error = DateValidator.validate_range(
            global_filters.date_range.start_date,
            global_filters.date_range.end_date
        )
        
        if not date_valid:
            logger.warning(f"Validación de fechas falló: {date_error}")
            return ACOperationResult(
                success=False,
                message=f"Error en rango de fechas: {date_error}"
            )

        # Validación especial: Consultas sin filtros
        date_range_days = (
            global_filters.date_range.end_date - 
            global_filters.date_range.start_date
        ).days

        filters_valid, filters_error, filters_warning = QueryWithoutFiltersValidator.validate(
            global_filters,
            specific_filters,
            date_range_days
        )

        if not filters_valid:
            logger.warning(f"Consulta sin filtros bloqueada: {filters_error}")
            return ACOperationResult(
                success=False,
                message=filters_error
            )

        if filters_warning:
            logger.info(f"Consulta sin filtros permitida con advertencia: {filters_warning}")
            # Continuar pero guardar advertencia para mostrar después

        # //: Validación 2: Al menos 1 filtro específico (Se elimino) 
        
        # Validación 3: Al menos 1 columna seleccionada
        if not columns or len(columns) == 0:
            logger.warning("No se seleccionaron columnas")
            return ACOperationResult(
                success=False,
                message="Debe seleccionar al menos 1 columna para exportar"
            )
        
        # Validación 4: Columnas válidas para normativa
        valid_columns = AC_EXPORT_COLUMNS.get(self.normativa, [])
        invalid_columns = [col for col in columns if col not in valid_columns]
        
        if invalid_columns:
            logger.warning(f"Columnas inválidas: {invalid_columns}")
            return ACOperationResult(
                success=False,
                message=f"Columnas inválidas para normativa {self.normativa}: {', '.join(invalid_columns)}"
            )
        
        # Validación 5: Validar rangos numéricos si existen
        if specific_filters.valor_consulta_min or specific_filters.valor_consulta_max:
            range_valid, range_error = ValueValidator.validate_numeric_range(
                specific_filters.valor_consulta_min,
                specific_filters.valor_consulta_max
            )
            
            if not range_valid:
                logger.warning(f"Validación de rango numérico falló: {range_error}")
                return ACOperationResult(   
                    success=False,
                    message=f"Error en filtro de valor consulta: {range_error}"
                )
        
        logger.info("Validación de inputs completada exitosamente")
        return ACOperationResult(success=True, message="Validación exitosa")
    
    def _generate_filename(self) -> str:
        """Genera nombre de archivo según nomenclatura."""
        timestamp = datetime.now().strftime('%Y%m%d')
        return f"RIPS_AC_{self.normativa}_{timestamp}.csv"
    
    def get_available_columns(self) -> List[str]:
        """Retorna lista de columnas disponibles para la normativa actual."""
        return AC_EXPORT_COLUMNS.get(self.normativa, [])
