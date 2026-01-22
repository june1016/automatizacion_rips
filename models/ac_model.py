"""Modelo de datos para tipo RIPS AC (Consultas)."""
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from models.base import FilterValue

logger = logging.getLogger(__name__)


@dataclass
class ACSpecificFilters:
    """Filtros específicos para AC (Consultas)."""
    finalidad_consulta: Optional[List[str]] = None
    causa_externa: Optional[List[str]] = None
    codigo_diagnostico_principal: Optional[List[str]] = None
    codigo_diagnostico_relacionado_1: Optional[List[str]] = None
    codigo_diagnostico_relacionado_2: Optional[List[str]] = None
    codigo_diagnostico_relacionado_3: Optional[List[str]] = None
    tipo_diagnostico_principal: Optional[List[str]] = None
    valor_consulta_min: Optional[float] = None
    valor_consulta_max: Optional[float] = None
    
    def to_filter_values(self) -> List[FilterValue]:
        """Convierte a lista de FilterValue para query builder."""
        filters = []
        
        if self.finalidad_consulta:
            filters.append(FilterValue('finalidad_consulta', 'IN', self.finalidad_consulta))
        
        if self.causa_externa:
            filters.append(FilterValue('causa_externa', 'IN', self.causa_externa))
        
        if self.tipo_diagnostico_principal:
            filters.append(FilterValue('tipo_diagnostico_principal', 'IN', self.tipo_diagnostico_principal))
        
        if self.codigo_diagnostico_principal:
            filters.append(FilterValue('codigo_diagnostico_principal', 'IN', self.codigo_diagnostico_principal))
        
        if self.codigo_diagnostico_relacionado_1:
            filters.append(FilterValue('codigo_diagnostico_relacionado_1', 'IN', self.codigo_diagnostico_relacionado_1))
        
        if self.codigo_diagnostico_relacionado_2:
            filters.append(FilterValue('codigo_diagnostico_relacionado_2', 'IN', self.codigo_diagnostico_relacionado_2))
        
        if self.codigo_diagnostico_relacionado_3:
            filters.append(FilterValue('codigo_diagnostico_relacionado_3', 'IN', self.codigo_diagnostico_relacionado_3))
        
        if self.valor_consulta_min is not None and self.valor_consulta_max is not None:
            filters.append(FilterValue('valor_consulta', 'BETWEEN', [self.valor_consulta_min, self.valor_consulta_max]))
        elif self.valor_consulta_min is not None:
            filters.append(FilterValue('valor_consulta', '>=', self.valor_consulta_min))
        elif self.valor_consulta_max is not None:
            filters.append(FilterValue('valor_consulta', '<=', self.valor_consulta_max))
        
        return filters


class ACFieldMapper:
    """Mapeo de campos AC entre normativas y conexiones."""
    
    # Tablas por conexión
    TABLES_BY_CONNECTION = {
        '67': {
            'main': 'cm_rips_ac_consultas',
            'cargas': 'cm_rips_cargas',
            'join_key_main': 'cm_rips_cargas_id',
            'join_key_cargas': 'id'
        },
        '38': {
            'main': 'rips.rips_ac_consulta',
            'cargas': None,
            'join_key_main': None,
            'join_key_cargas': None
        },
        '39': {
            'main': 'cm_rips_consultas',
            'cargas': None,
            'join_key_main': None,
            'join_key_cargas': None
        },
        '82': {
            'main': 'cm_fe_rips_consultas',
            'cargas': 'cm_fe_rips_cargas',
            'join_key_main': 'id_carga',
            'join_key_cargas': 'id'
        }
    }
    
    # Mapeo de campos estándar (3374) a nombres REALES por conexión
    FIELD_MAPPING_BY_CONNECTION = {
        '67': {
            'numero_factura': 'num_factura',
            'codigo_prestador': 'codigo_reps',
            'tipo_documento': 'mae_tipo_documento_codigo',
            'documento': 'documento_afiliado',
            'fecha_consulta': 'fecha_consulta',
            'numero_autorizacion': 'autorizacion',
            'codigo_consulta': 'ma_tecnologia_codigo',
            'finalidad_consulta': 'mae_finalidad_consulta_codigo',
            'causa_externa': 'mae_causa_externa_codigo',
            'codigo_diagnostico_principal': 'ma_diagnostico_principal_codigo',
            'codigo_diagnostico_relacionado_1': 'ma_diagnostico_relacionado1_codigo',
            'codigo_diagnostico_relacionado_2': 'ma_diagnostico_relacionado2_codigo',
            'codigo_diagnostico_relacionado_3': 'ma_diagnostico_relacionado3_codigo',
            'tipo_diagnostico_principal': 'mae_tipo_diagnostico_codigo',
            'valor_consulta': 'valor_consulta',
            'valor_cuota_moderadora': 'valor_cuota_moderadora',
            'valor_neto_pagar': 'valor_a_pagar'
        },
        '38': {
            'numero_factura': 'numero_factura',
            'codigo_prestador': 'codigo_ips_sede',
            'tipo_documento': 'codigo_tipo_identificacion',
            'documento': 'numero_identificacion',
            'fecha_consulta': 'fecha_consulta',
            'numero_autorizacion': 'numero_autorizacion',
            'codigo_consulta': 'codigo_consulta',
            'finalidad_consulta': 'codigo_finalidad',
            'causa_externa': 'codigo_causa_externa',
            'codigo_diagnostico_principal': 'codigo_diagnostico_principal',
            'codigo_diagnostico_relacionado_1': 'codigo_diagnostico_relacionado1',
            'codigo_diagnostico_relacionado_2': 'codigo_diagnostico_relacionado2',
            'codigo_diagnostico_relacionado_3': 'codigo_diagnostico_relacionado3',
            'tipo_diagnostico_principal': 'codigo_tipo_diagnostico',
            'valor_consulta': 'valor_consulta',
            'valor_cuota_moderadora': 'valor_cuota_moderadora',
            'valor_neto_pagar': 'valor_neto'
        },
        '39': {
            'numero_factura': 'num_factura',
            'codigo_prestador': 'cod_prestador',
            'tipo_documento': 'cod_tipo_documento',
            'documento': 'documento_afiliado',
            'fecha_consulta': 'fec_consulta',
            'numero_autorizacion': 'autorizacion',
            'codigo_consulta': 'cod_servicio',
            'finalidad_consulta': 'finalidad_consulta',
            'causa_externa': 'causa_externa',
            'codigo_diagnostico_principal': 'cod_diagnostico_ppal',
            'codigo_diagnostico_relacionado_1': 'cod_diagnostico_relacionado1',
            'codigo_diagnostico_relacionado_2': 'cod_diagnostico_relacionado2',
            'codigo_diagnostico_relacionado_3': 'cod_diagnostico_relacionado3',
            'tipo_diagnostico_principal': 'id_tipo_diagnostico',
            'valor_consulta': 'valor_consulta',
            'valor_cuota_moderadora': 'valor_cuota_moderadora',
            'valor_neto_pagar': 'valor_a_pagar'
        }
    }
    
    # Mapeo 3374 -> 2275 (solo para nombres de columnas en export)
    FIELD_MAPPING_3374_TO_2275 = {
        'numero_factura': 'numero_factura',
        'codigo_prestador': 'codigo_habilitacion_prestador',
        'tipo_documento': 'tipo_documento_usuario',
        'documento': 'numero_documento_usuario',
        'fecha_consulta': 'fecha_inicio_atencion',
        'numero_autorizacion': 'numero_autorizacion',
        'codigo_consulta': 'codigo_servicio',
        'finalidad_consulta': 'finalidad_atencion',
        'causa_externa': 'causa_externa',
        'codigo_diagnostico_principal': 'codigo_diagnostico_principal',
        'codigo_diagnostico_relacionado_1': 'codigo_diagnostico_relacionado_1',
        'codigo_diagnostico_relacionado_2': 'codigo_diagnostico_relacionado_2',
        'codigo_diagnostico_relacionado_3': 'codigo_diagnostico_relacionado_3',
        'tipo_diagnostico_principal': 'tipo_diagnostico_principal',
        'valor_consulta': 'valor_servicio',
        'valor_cuota_moderadora': 'valor_cuota_moderadora',
        'valor_neto_pagar': 'valor_total_copago'
    }
    
    @classmethod
    def get_real_field_name(cls, standard_field: str, connection_id: str) -> str:
        """
        Traduce nombre de campo estándar a nombre real en la BD.
        
        Args:
            standard_field: Nombre estándar del campo (ej: 'codigo_prestador')
            connection_id: ID de conexión (ej: '67')
            
        Returns:
            Nombre real del campo en la BD (ej: 'codigo_reps')
        """
        mapping = cls.FIELD_MAPPING_BY_CONNECTION.get(connection_id, {})
        return mapping.get(standard_field, standard_field)
    
    @classmethod
    def get_table_config(cls, connection_id: str) -> Dict[str, str]:
        """Obtiene configuración de tablas para una conexión."""
        return cls.TABLES_BY_CONNECTION.get(connection_id, {})
    
    @classmethod
    def map_field_for_export(cls, field_name: str, from_normativa: str, to_normativa: str) -> str:
        """Mapea nombre de campo para exportación entre normativas."""
        if from_normativa == to_normativa:
            return field_name
        
        if from_normativa == '3374' and to_normativa == '2275':
            return cls.FIELD_MAPPING_3374_TO_2275.get(field_name, field_name)
        
        if from_normativa == '2275' and to_normativa == '3374':
            reverse_map = {v: k for k, v in cls.FIELD_MAPPING_3374_TO_2275.items()}
            return reverse_map.get(field_name, field_name)
        
        return field_name
    
    @classmethod
    def get_column_name_mapping(cls, connection_id: str) -> Dict[str, str]:
        """
        Obtiene mapeo de nombres reales a nombres estandarizados.
        
        Returns:
            Dict[nombre_real] = nombre_estandarizado
        
        Ejemplo para conexión '67':
            {'codigo_reps': 'codigo_prestador',
             'mae_tipo_documento_codigo': 'tipo_documento',
             'documento_afiliado': 'documento', ...}
        """
        # Obtener el mapeo específico para esta conexión
        connection_mapping = cls.FIELD_MAPPING_BY_CONNECTION.get(connection_id, {})
        
        if not connection_mapping:
            logger.warning(f"No se encontró mapeo para conexión {connection_id}")
            return {}
        
        # Invertir el mapeo: de {standard: real} a {real: standard}
        mapping = {}
        for standard_field, real_field in connection_mapping.items():
            mapping[real_field] = standard_field
        
        return mapping


# Columnas disponibles para exportación
AC_EXPORT_COLUMNS = {
    '3374': [
        'numero_factura',
        'codigo_prestador',
        'tipo_documento',
        'documento',
        'fecha_consulta',
        'numero_autorizacion',
        'codigo_consulta',
        'finalidad_consulta',
        'causa_externa',
        'codigo_diagnostico_principal',
        'codigo_diagnostico_relacionado_1',
        'codigo_diagnostico_relacionado_2',
        'codigo_diagnostico_relacionado_3',
        'tipo_diagnostico_principal',
        'valor_consulta',
        'valor_cuota_moderadora',
        'valor_neto_pagar'
    ],
    '2275': [
        'numero_factura',
        'codigo_habilitacion_prestador',
        'tipo_documento_usuario',
        'numero_documento_usuario',
        'fecha_inicio_atencion',
        'numero_autorizacion',
        'codigo_servicio',
        'finalidad_atencion',
        'causa_externa',
        'codigo_diagnostico_principal',
        'codigo_diagnostico_relacionado_1',
        'codigo_diagnostico_relacionado_2',
        'codigo_diagnostico_relacionado_3',
        'tipo_diagnostico_principal',
        'valor_servicio',
        'valor_cuota_moderadora',
        'valor_total_copago'
    ]
}