"""Manejo de archivos para carga de valores en filtros."""
import logging
from typing import List, Optional, Tuple
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)

# Límites técnicos
MAX_FILE_SIZE_MB = 2
MAX_VALUES_FROM_FILE = 1_000


class FileHandler:
    """Handler para lectura de archivos de valores."""
    
    SUPPORTED_EXTENSIONS = ['.xlsx', '.xls', '.csv', '.txt']
    
    @staticmethod
    def read_values_from_file(
        filepath: str,
        separator: Optional[str] = None
    ) -> Tuple[bool, Optional[List[str]], Optional[str]]:
        """
        Lee valores desde archivo.
        
        Args:
            filepath: Ruta del archivo
            separator: Separador para CSV/TXT. Si None, intenta detectar automáticamente
        
        Returns:
            tuple: (success, values_list, error_message)
        """
        try:
            # Validar extensión
            file_path = Path(filepath)
            
            if not file_path.exists():
                return False, None, "Archivo no encontrado"
            
            extension = file_path.suffix.lower()
            
            if extension not in FileHandler.SUPPORTED_EXTENSIONS:
                return False, None, f"Formato no soportado. Use: {', '.join(FileHandler.SUPPORTED_EXTENSIONS)}"
            
            # Validar tamaño
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            
            if file_size_mb > MAX_FILE_SIZE_MB:
                return False, None, f"Archivo excede tamaño máximo de {MAX_FILE_SIZE_MB}MB"
            
            # Leer según extensión
            if extension in ['.xlsx', '.xls']:
                values = FileHandler._read_excel(filepath)
            elif extension in ['.csv', '.txt']:
                values = FileHandler._read_text_file(filepath, separator)
            else:
                return False, None, f"Extensión no reconocida: {extension}"
            
            # Validar cantidad de valores
            if len(values) > MAX_VALUES_FROM_FILE:
                return False, None, f"Archivo contiene {len(values)} valores. Máximo permitido: {MAX_VALUES_FROM_FILE}"
            
            if len(values) == 0:
                return False, None, "Archivo no contiene valores válidos"
            
            logger.info(f"Archivo leído exitosamente: {len(values)} valores")
            return True, values, None
            
        except Exception as e:
            logger.error(f"Error leyendo archivo: {str(e)}")
            return False, None, f"Error leyendo archivo: {str(e)}"
    
    @staticmethod
    def _read_excel(filepath: str) -> List[str]:
        """Lee valores desde archivo Excel (primera columna, sin header)."""
        df = pd.read_excel(filepath, header=None)
        
        # Tomar primera columna
        values = df.iloc[:, 0].astype(str).tolist()
        
        # Limpiar valores
        values = FileHandler._clean_values(values)
        
        return values
    
    @staticmethod
    def _read_text_file(filepath: str, separator: Optional[str]) -> List[str]:
        """Lee valores desde archivo CSV/TXT."""
        
        # Intentar detectar separador si no se proporciona
        if separator is None:
            separator = FileHandler._detect_separator(filepath)
            logger.info(f"Separador detectado automáticamente: '{separator}'")
        
        # Si separador es salto de línea, leer línea por línea
        if separator == '\n':
            with open(filepath, 'r', encoding='utf-8') as f:
                values = [line.strip() for line in f]
        else:
            # Leer como CSV con separador específico
            df = pd.read_csv(filepath, sep=separator, header=None, encoding='utf-8')
            
            # Tomar primera columna
            values = df.iloc[:, 0].astype(str).tolist()
        
        # Limpiar valores
        values = FileHandler._clean_values(values)
        
        return values
    
    @staticmethod
    def _detect_separator(filepath: str) -> str:
        """
        Detecta separador en archivo CSV/TXT.
        
        Estrategia:
        1. Lee primeras líneas
        2. Cuenta ocurrencias de ',', '|', '\n'
        3. Retorna el más frecuente
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            sample = f.read(1024)  # Leer primeros 1KB
        
        # Contar separadores
        comma_count = sample.count(',')
        pipe_count = sample.count('|')
        newline_count = sample.count('\n')
        
        # Si hay muchos saltos de línea y pocos separadores → un valor por línea
        if newline_count > 5 and comma_count < 3 and pipe_count < 3:
            return '\n'
        
        # Si hay más comas que pipes
        if comma_count > pipe_count:
            return ','
        
        # Si hay más pipes que comas
        if pipe_count > comma_count:
            return '|'
        
        # Por defecto, asumir salto de línea
        return '\n'
    
    @staticmethod
    def _clean_values(values: List[str]) -> List[str]:
        """
        Limpia lista de valores.
        
        - Trim espacios
        - Eliminar vacíos
        - Eliminar duplicados
        - Mantener orden
        """
        cleaned = []
        seen = set()
        
        for value in values:
            # Trim
            value = str(value).strip()
            
            # Saltar vacíos y 'nan' (de pandas)
            if not value or value.lower() in ['nan', 'none', '']:
                continue
            
            # Saltar duplicados
            if value in seen:
                continue
            
            cleaned.append(value)
            seen.add(value)
        
        return cleaned
    
    @staticmethod
    def validate_file_before_upload(
        filename: str,
        file_size_bytes: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida archivo antes de subirlo (desde UI).
        
        Args:
            filename: Nombre del archivo
            file_size_bytes: Tamaño en bytes
        
        Returns:
            tuple: (is_valid, error_message)
        """
        # Validar extensión
        extension = Path(filename).suffix.lower()
        
        if extension not in FileHandler.SUPPORTED_EXTENSIONS:
            return False, f"Formato no soportado. Use: {', '.join(FileHandler.SUPPORTED_EXTENSIONS)}"
        
        # Validar tamaño
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        if file_size_mb > MAX_FILE_SIZE_MB:
            return False, f"Archivo excede tamaño máximo de {MAX_FILE_SIZE_MB}MB"
        
        return True, None


class ValueListParser:
    """Parser para entrada de lista/textarea."""
    
    @staticmethod
    def parse_from_text(text: str, separator: Optional[str] = None) -> List[str]:
        """
        Parsea valores desde texto (textarea).
        
        Args:
            text: Texto con valores
            separator: Separador. Si None, detecta automáticamente
        
        Returns:
            Lista de valores limpios
        """
        if not text or text.strip() == '':
            return []
        
        # Detectar separador si no se proporciona
        if separator is None:
            separator = ValueListParser._detect_text_separator(text)
        
        # Separar valores
        if separator == '\n':
            values = text.split('\n')
        elif separator == ',':
            values = text.split(',')
        elif separator == '|':
            values = text.split('|')
        elif separator == ' ':  # ← NUEVO: soportar espacios
            values = text.split()
        else:
            # Fallback: asumir salto de línea
            values = text.split('\n')
        
        # Limpiar
        values = FileHandler._clean_values(values)
        
        return values

    @staticmethod
    def _detect_text_separator(text: str) -> str:
        """Detecta separador en texto."""
        newline_count = text.count('\n')
        comma_count = text.count(',')
        pipe_count = text.count('|')
        space_count = text.count(' ')
        
        # Contar palabras únicas (para detectar si son valores separados por espacio)
        words = text.split()
        
        # Si hay muchos espacios y pocas líneas → valores separados por espacio
        if space_count > 5 and newline_count < 3:
            return ' '
        
        # Más saltos de línea → un valor por línea
        if newline_count >= comma_count and newline_count >= pipe_count:
            return '\n'
        
        # Más comas
        if comma_count > pipe_count:
            return ','
        
        # Más pipes
        return '|'