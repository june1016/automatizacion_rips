"""Constructor de queries SQL para extracción multi-conexión."""
import logging
from typing import List, Dict, Any
from models.base import GlobalFilters
from models.ac_model import ACFieldMapper, ACSpecificFilters

logger = logging.getLogger(__name__)


class ACQueryBuilder:
    """Constructor de queries para tipo RIPS AC."""
    
    def __init__(self, normativa: str):
        self.normativa = normativa
        self.mapper = ACFieldMapper()
    
    def build_query(
        self,
        connection_id: str,
        global_filters: GlobalFilters,
        specific_filters: ACSpecificFilters,
        columns: List[str]
    ) -> tuple[str, Dict[str, Any]]:
        """Construye query SQL para una conexión específica."""
        
        table_config = self.mapper.get_table_config(connection_id)
        
        select_clause = self._build_select_clause(columns, connection_id)
        from_clause = self._build_from_clause(table_config, connection_id)
        where_clause, params = self._build_where_clause(
            global_filters,
            specific_filters,
            table_config,
            connection_id
        )
        
        query = f"""
        {select_clause}
        {from_clause}
        {where_clause}
        """
        
        logger.info("=" * 80)
        logger.info("QUERY CONSTRUIDO:")
        logger.info(query)
        logger.info("-" * 80)
        logger.info("PARÁMETROS:")
        for key, value in params.items():
            logger.info(f"  {key}: {value}")
        logger.info("=" * 80)
        
        logger.info(f"Query construido para conexión {connection_id}")
        return query, params
    
    def _build_select_clause(self, columns: List[str], connection_id: str) -> str:
        """Construye cláusula SELECT con mapeo de campos."""
        
        table_config = self.mapper.get_table_config(connection_id)
        main_table = table_config['main']
        
        mapped_columns = []
        for col in columns:
            real_field = self.mapper.get_real_field_name(col, connection_id)
            mapped_columns.append(f"{main_table}.{real_field}")
        
        columns_str = ",\n    ".join(mapped_columns)
        return f"SELECT\n    {columns_str}"
    
    def _build_from_clause(self, table_config: Dict[str, str], connection_id: str) -> str:
        """Construye cláusula FROM con JOINs si aplica."""
        
        main_table = table_config['main']
        cargas_table = table_config.get('cargas')
        
        from_clause = f"FROM {main_table}"
        
        if cargas_table and connection_id in ['67', '82']:
            join_key_main = table_config['join_key_main']
            join_key_cargas = table_config['join_key_cargas']
            from_clause += f"\nINNER JOIN {cargas_table} ON {main_table}.{join_key_main} = {cargas_table}.{join_key_cargas}"
        
        return from_clause
    
    def _build_where_clause(
        self,
        global_filters: GlobalFilters,
        specific_filters: ACSpecificFilters,
        table_config: Dict[str, str],
        connection_id: str
    ) -> tuple[str, Dict[str, Any]]:
        """Construye cláusula WHERE con todos los filtros."""
        
        conditions = []
        params = {}
        main_table = table_config['main']
        cargas_table = table_config.get('cargas')
        
        # Filtro de fecha (obligatorio)
        fecha_field = self.mapper.get_real_field_name('fecha_consulta', connection_id)
        conditions.append(f"{main_table}.{fecha_field} BETWEEN :fecha_inicio AND :fecha_fin")
        params['fecha_inicio'] = global_filters.date_range.start_date
        params['fecha_fin'] = global_filters.date_range.end_date
        
        # Filtro de estado según conexión
        if connection_id == '67' and cargas_table:
            conditions.append(f"{cargas_table}.estado = 7")
        
        # Filtros globales opcionales
        if global_filters.codigo_prestador:
            prestador_field = self.mapper.get_real_field_name('codigo_prestador', connection_id)
            conditions.append(f"{main_table}.{prestador_field} IN :param_codigo_prestador")
            params['param_codigo_prestador'] = tuple(global_filters.codigo_prestador)
        
        if global_filters.documento_usuario:
            documento_field = self.mapper.get_real_field_name('documento', connection_id)
            conditions.append(f"{main_table}.{documento_field} IN :param_documento")
            params['param_documento'] = tuple(global_filters.documento_usuario)
        
        # Filtros específicos de AC
        self._add_specific_filters(
            specific_filters,
            conditions,
            params,
            main_table,
            connection_id
        )
        
        where_clause = "WHERE\n    " + "\n    AND ".join(conditions)
        
        return where_clause, params
    
    def _add_specific_filters(
        self,
        specific_filters: ACSpecificFilters,
        conditions: List[str],
        params: Dict[str, Any],
        main_table: str,
        connection_id: str
    ):
        """Agrega filtros específicos de AC con lógica correcta."""
        
        # Filtros categóricos simples (AND normal)
        if specific_filters.finalidad_consulta:
            field = self.mapper.get_real_field_name('finalidad_consulta', connection_id)
            conditions.append(f"{main_table}.{field} IN :param_finalidad_consulta")
            params['param_finalidad_consulta'] = tuple(specific_filters.finalidad_consulta)
        
        if specific_filters.causa_externa:
            field = self.mapper.get_real_field_name('causa_externa', connection_id)
            conditions.append(f"{main_table}.{field} IN :param_causa_externa")
            params['param_causa_externa'] = tuple(specific_filters.causa_externa)
        
        if specific_filters.tipo_diagnostico_principal:
            field = self.mapper.get_real_field_name('tipo_diagnostico_principal', connection_id)
            conditions.append(f"{main_table}.{field} IN :param_tipo_diagnostico_principal")
            params['param_tipo_diagnostico_principal'] = tuple(specific_filters.tipo_diagnostico_principal)
        
        # LÓGICA ESPECIAL: Diagnósticos con OR
        diagnostico_conditions = []
        
        if specific_filters.codigo_diagnostico_principal:
            field = self.mapper.get_real_field_name('codigo_diagnostico_principal', connection_id)
            diagnostico_conditions.append(f"{main_table}.{field} IN :param_codigo_diagnostico_principal")
            params['param_codigo_diagnostico_principal'] = tuple(specific_filters.codigo_diagnostico_principal)
        
        if specific_filters.codigo_diagnostico_relacionado_1:
            field = self.mapper.get_real_field_name('codigo_diagnostico_relacionado_1', connection_id)
            diagnostico_conditions.append(f"{main_table}.{field} IN :param_codigo_diagnostico_relacionado_1")
            params['param_codigo_diagnostico_relacionado_1'] = tuple(specific_filters.codigo_diagnostico_relacionado_1)
        
        if specific_filters.codigo_diagnostico_relacionado_2:
            field = self.mapper.get_real_field_name('codigo_diagnostico_relacionado_2', connection_id)
            diagnostico_conditions.append(f"{main_table}.{field} IN :param_codigo_diagnostico_relacionado_2")
            params['param_codigo_diagnostico_relacionado_2'] = tuple(specific_filters.codigo_diagnostico_relacionado_2)
        
        if specific_filters.codigo_diagnostico_relacionado_3:
            field = self.mapper.get_real_field_name('codigo_diagnostico_relacionado_3', connection_id)
            diagnostico_conditions.append(f"{main_table}.{field} IN :param_codigo_diagnostico_relacionado_3")
            params['param_codigo_diagnostico_relacionado_3'] = tuple(specific_filters.codigo_diagnostico_relacionado_3)
        
        # Si hay al menos un filtro de diagnóstico, agrupar con OR
        if diagnostico_conditions:
            grouped_condition = "(" + "\n        OR ".join(diagnostico_conditions) + ")"
            conditions.append(grouped_condition)
        
        # Filtro de rango de valor
        if specific_filters.valor_consulta_min is not None and specific_filters.valor_consulta_max is not None:
            field = self.mapper.get_real_field_name('valor_consulta', connection_id)
            conditions.append(f"{main_table}.{field} BETWEEN :valor_consulta_min AND :valor_consulta_max")
            params['valor_consulta_min'] = specific_filters.valor_consulta_min
            params['valor_consulta_max'] = specific_filters.valor_consulta_max
        elif specific_filters.valor_consulta_min is not None:
            field = self.mapper.get_real_field_name('valor_consulta', connection_id)
            conditions.append(f"{main_table}.{field} >= :valor_consulta_min")
            params['valor_consulta_min'] = specific_filters.valor_consulta_min
        elif specific_filters.valor_consulta_max is not None:
            field = self.mapper.get_real_field_name('valor_consulta', connection_id)
            conditions.append(f"{main_table}.{field} <= :valor_consulta_max")
            params['valor_consulta_max'] = specific_filters.valor_consulta_max
    
    def estimate_record_count(
        self,
        connection_id: str,
        global_filters: GlobalFilters,
        specific_filters: ACSpecificFilters
    ) -> tuple[str, Dict[str, Any]]:
        """Estima cantidad de registros (COUNT) antes de ejecutar query completo."""
        
        table_config = self.mapper.get_table_config(connection_id)
        
        from_clause = self._build_from_clause(table_config, connection_id)
        where_clause, params = self._build_where_clause(
            global_filters,
            specific_filters,
            table_config,
            connection_id
        )
        
        query = f"""
        SELECT COUNT(*) as total
        {from_clause}
        {where_clause}
        """
        
        return query, params