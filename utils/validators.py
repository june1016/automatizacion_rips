"""Validadores de datos y reglas de negocio."""
from datetime import date, datetime
from typing import List, Optional, Any
from config.settings import MAX_RECORDS, MAX_MANUAL_VALUES, MAX_LIST_VALUES


class DateValidator:
    """Validador de fechas."""
    
    @staticmethod
    def validate_range(start_date: date, end_date: date) -> tuple[bool, Optional[str]]:
        """Valida rango de fechas según reglas de negocio."""
        from config.settings import MAX_DATE_RANGE_DAYS, MAX_DATE_RANGE_YEARS
        
        # Fecha inicio <= fecha fin
        if start_date > end_date:
            return False, "Fecha inicio debe ser menor o igual a fecha fin"
        
        # No fechas futuras
        today = date.today()
        if start_date > today or end_date > today:
            return False, "No se permiten fechas futuras"
        
        # Rango máximo 3 años
        days_diff = (end_date - start_date).days
        if days_diff > MAX_DATE_RANGE_DAYS:
            return False, f"Rango máximo permitido: {MAX_DATE_RANGE_YEARS} años"
        
        return True, None
    
    @staticmethod
    def parse_date(date_str: str) -> Optional[date]:
        """Convierte string a date."""
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None

class ValueValidator:
    """Validador de valores de filtros."""
    
    @staticmethod
    def validate_multiple_values(values: List[Any], mode: str) -> tuple[bool, Optional[str]]:
        """Valida lista de valores según modo de entrada."""
        
        if not values:
            return False, "Debe proporcionar al menos un valor"
        
        value_count = len(values)
        
        if mode == 'manual' and value_count > MAX_MANUAL_VALUES:
            return False, f"Modo manual: máximo {MAX_MANUAL_VALUES} valores"
        
        if mode in ['lista', 'archivo'] and value_count > MAX_LIST_VALUES:
            return False, f"Modo {mode}: máximo {MAX_LIST_VALUES} valores"
        
        return True, None
    
    @staticmethod
    def validate_numeric_range(min_val: Optional[float], max_val: Optional[float]) -> tuple[bool, Optional[str]]:
        """Valida rango numérico."""
        
        if min_val is not None and min_val < 0:
            return False, "Valor mínimo no puede ser negativo"
        
        if max_val is not None and max_val < 0:
            return False, "Valor máximo no puede ser negativo"
        
        if min_val is not None and max_val is not None and min_val > max_val:
            return False, "Valor mínimo debe ser menor o igual al máximo"
        
        return True, None
    
    @staticmethod
    def validate_non_empty(value: Any) -> tuple[bool, Optional[str]]:
        """Valida que el valor no esté vacío."""
        
        if value is None or value == '' or (isinstance(value, list) and len(value) == 0):
            return False, "El valor no puede estar vacío"
        
        return True, None

class RecordCountValidator:
    """Validador de límites de registros."""
    
    @staticmethod
    def check_limit(estimated_count: int) -> tuple[str, Optional[str]]:
        """
        Valida cantidad de registros estimados.
        
        Returns:
            tuple: (level, message)
                level: 'ok' | 'warning' | 'error'
        """
        
        if estimated_count > MAX_RECORDS:
            return 'error', f"Consulta excede límite de {MAX_RECORDS:,} registros"
        
        if estimated_count > 100_000:
            return 'warning', f"Consulta grande ({estimated_count:,} registros). Puede tardar varios minutos"
        
        return 'ok', None
    
class CodigoPrestadorValidator:
    """Validador para códigos de prestador (10-12 dígitos numéricos)."""
    
    MIN_LENGTH = 10
    MAX_LENGTH = 12
    
    @staticmethod
    def validate(values: List[str]) -> tuple[bool, List[str], Optional[str]]:
        """
        Valida códigos de prestador sin modificarlos.
        
        Reglas:
        - Solo dígitos numéricos
        - Longitud entre 10 y 12 dígitos
        - No se aplica padding ni corrección automática
        
        Args:
            values: Lista de códigos a validar
        
        Returns:
            tuple: (success, validated_values, error_message)
        """
        if not values:
            return True, [], None
        
        validated = []
        invalid = []
        
        for value in values:
            value_clean = str(value).strip()
            
            # # Validar que sea numérico
            # if not value_clean.isdigit():
            #     invalid.append(f"'{value}' (contiene caracteres no numéricos)")
            #     continue
            
            # Validar longitud
            length = len(value_clean)
            if CodigoPrestadorValidator.MIN_LENGTH <= length <= CodigoPrestadorValidator.MAX_LENGTH:
                validated.append(value_clean)
            else:
                invalid.append(f"'{value}' ({length} dígitos)")
        
        # Construir mensaje de error si hay valores inválidos
        if invalid:
            invalid_str = ', '.join(invalid[:5])
            if len(invalid) > 5:
                invalid_str += f" y {len(invalid) - 5} más"
            
            return (
                False, 
                [], 
                f"Códigos inválidos detectados: {invalid_str}. "
                f"Los códigos deben tener entre {CodigoPrestadorValidator.MIN_LENGTH}-{CodigoPrestadorValidator.MAX_LENGTH} dígitos."
            )
        
        return True, validated, None

class QueryWithoutFiltersValidator:
    """Validador para consultas sin filtros específicos."""
    
    @staticmethod
    def validate(
        global_filters: Any,
        specific_filters: Any,
        date_range_days: int
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Valida consultas sin filtros para prevenir consultas masivas.
        
        Args:
            global_filters: Filtros globales (prestador, documento)
            specific_filters: Filtros específicos del tipo RIPS
            date_range_days: Días del rango de fechas
        
        Returns:
            tuple: (success, error_message, warning_message)
                - success: False para bloquear, True para permitir
                - error_message: Mensaje de error si se bloquea
                - warning_message: Advertencia si se permite con condiciones
        """
        # Detectar si hay filtros globales
        has_global_filters = any([
            global_filters.codigo_prestador,
            global_filters.documento_usuario
        ])
        
        # Detectar si hay filtros específicos (intentar acceder a atributos comunes)
        has_specific_filters = False
        try:
            # Para AC específicamente
            has_specific_filters = any([
                getattr(specific_filters, 'finalidad_consulta', None),
                getattr(specific_filters, 'causa_externa', None),
                getattr(specific_filters, 'codigo_diagnostico_principal', None),
                getattr(specific_filters, 'codigo_diagnostico_relacionado_1', None),
                getattr(specific_filters, 'codigo_diagnostico_relacionado_2', None),
                getattr(specific_filters, 'codigo_diagnostico_relacionado_3', None),
                getattr(specific_filters, 'tipo_diagnostico_principal', None),
                getattr(specific_filters, 'valor_consulta_min', None) is not None,
                getattr(specific_filters, 'valor_consulta_max', None) is not None
            ])
        except:
            pass
        
        # Si NO hay ningún filtro
        if not has_global_filters and not has_specific_filters:
            
            # Rango muy corto (<=3 meses): Permitir sin advertencia
            if date_range_days <= 90:
                return True, None, None
            
            # Rango medio (3-12 meses): Advertencia
            elif date_range_days <= 365:
                warning = (
                    f"Consulta sin filtros abarca {date_range_days} días. "
                    "Puede tardar varios minutos y retornar muchos registros."
                )
                return True, None, warning
            
            # Rango largo (1-2 años): Advertencia fuerte
            elif date_range_days <= 730:
                warning = (
                    f"⚠️ Consulta sin filtros abarca {date_range_days} días (~{date_range_days//365} años). "
                    "Esto puede tardar 5-10 minutos y exceder límites de registros. "
                    "Recomendación: Agregue filtros (prestador, diagnóstico, etc.)"
                )
                return True, None, warning
            
            # Rango muy largo (>2 años): Bloquear
            else:
                error = (
                    f"Consulta sin filtros excede el límite seguro. "
                    f"Rango: {date_range_days} días (~{date_range_days//365} años). "
                    "Debe agregar al menos un filtro (código prestador, documento usuario, "
                    "diagnóstico, etc.) o reducir el rango a máximo 2 años."
                )
                return False, error, None
        
        # Si hay filtros, permitir sin restricciones adicionales
        return True, None, None