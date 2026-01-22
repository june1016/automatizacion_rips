"""Modelos base y estructuras de datos comunes."""
from dataclasses import dataclass
from datetime import date
from typing import Optional, List, Dict, Any


@dataclass
class DateRange:
    """Rango de fechas para filtros."""
    start_date: date
    end_date: date
    
    def get_connections(self) -> List[str]:
        """Determina qué conexiones consultar según el rango de fechas."""
        year_start = self.start_date.year
        year_end = self.end_date.year
        
        # Conexión 67 siempre se consulta
        connections = ['67']
        
        # Si incluye 2020, agregar 38 y 39
        if year_start <= 2020 <= year_end:
            connections.extend(['38', '39'])
        
        # Si rango 2013-2019, agregar 39
        elif year_end < 2020 and year_start >= 2013:
            connections.append('39')
        
        return connections

@dataclass
class FilterValue:
    """Valor de filtro con operador."""
    field: str
    operator: str
    value: Any
    
    def to_sql_condition(self, table_prefix: str = None) -> tuple[str, Dict]:
        """
        Convierte a condición SQL parametrizada.
        
        Args:
            table_prefix: Prefijo de tabla (ej: 'cm_rips_consultas')
        """
        # Extraer nombre limpio del campo (sin prefijo de tabla si existe)
        field_name = self.field.split('.')[-1] if '.' in self.field else self.field
        
        # Construir nombre completo del campo con prefijo si se proporciona
        full_field = f"{table_prefix}.{field_name}" if table_prefix else field_name
        
        # Nombre del parámetro (solo el nombre del campo, sin tabla)
        param_name = f"param_{field_name}"
        
        if self.operator == 'IN':
            condition = f"{full_field} IN :param_{field_name}"
            params = {f"param_{field_name}": tuple(self.value)}
            
        elif self.operator == 'BETWEEN':
            condition = f"{full_field} BETWEEN :param_{field_name}_start AND :param_{field_name}_end"
            params = {
                f"param_{field_name}_start": self.value[0],
                f"param_{field_name}_end": self.value[1]
            }
            
        elif self.operator in ['=', '>', '<', '>=', '<=', '!=']:
            condition = f"{full_field} {self.operator} :param_{field_name}"
            params = {f"param_{field_name}": self.value}
            
        else:
            raise ValueError(f"Operador no soportado: {self.operator}")
        
        return condition, params

@dataclass
class GlobalFilters:
    """Filtros globales aplicables a todos los tipos RIPS."""
    date_range: DateRange
    codigo_prestador: Optional[List[str]] = None
    documento_usuario: Optional[List[str]] = None


@dataclass
class QueryResult:
    """Resultado de consulta con metadatos."""
    data: List[Dict[str, Any]]
    record_count: int
    connections_used: List[str]
    execution_time: float
    columns: List[str]