"""Procesamiento y consolidación de datos multi-conexión."""
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
from config.database import db_connections
from models.base import QueryResult
from models.ac_model import ACFieldMapper
from utils.catalogs import CatalogNormalizer
from sqlalchemy import text
import time

logger = logging.getLogger(__name__)


class ACDataProcessor:
    """Procesador de datos para tipo RIPS AC."""
    
    def __init__(self, normativa: str):
        self.normativa = normativa
        self.normalizer = CatalogNormalizer()
        self.mapper = ACFieldMapper()
    
    def execute_and_consolidate(
        self,
        queries: Dict[str, tuple[str, Dict[str, Any]]]
    ) -> QueryResult:
        """
        Ejecuta queries en múltiples conexiones y consolida resultados.
        
        Args:
            queries: Dict[connection_id] = (query_string, params)
        
        Returns:
            QueryResult con datos consolidados y enriquecidos
        """
        start_time = time.time()
        all_dataframes = []
        connections_used = []
        
        for conn_id, (query, params) in queries.items():
            logger.info(f"Ejecutando query en conexión {conn_id}")
            
            try:
                session = db_connections.get_session(conn_id)
                
                result = session.execute(text(query), params)
                rows = result.fetchall()
                columns = result.keys()
                
                session.close()
                
                if rows:
                    df = pd.DataFrame(rows, columns=columns)
                    
                    # Renombrar columnas a nombres estandarizados
                    df = self._rename_columns_to_standard(df, conn_id)

                    # Normalizar fecha_consulta a tipo date (sin hora)
                    if 'fecha_consulta' in df.columns:
                        df['fecha_consulta'] = pd.to_datetime(
                            df['fecha_consulta'],
                            errors='coerce'
                        ).dt.date
                    
                    all_dataframes.append(df)
                    connections_used.append(conn_id)
                    
                    logger.info(f"Conexión {conn_id}: {len(df)} registros obtenidos")
                else:
                    logger.info(f"Conexión {conn_id}: sin registros")
                    
            except Exception as e:
                logger.error(f"Error en conexión {conn_id}: {str(e)}")
                raise
        
        if not all_dataframes:
            logger.warning("No se obtuvieron datos de ninguna conexión")
            return QueryResult(
                data=[],
                record_count=0,
                connections_used=connections_used,
                execution_time=time.time() - start_time,
                columns=[]
            )
        
        # Consolidar DataFrames verticalmente
        consolidated_df = pd.concat(all_dataframes, ignore_index=True)
        logger.info(f"Total registros antes de limpieza: {len(consolidated_df)}")
        
        # Normalizar valores categóricos
        consolidated_df = self._normalize_categorical_fields(consolidated_df)
        
        # Eliminar duplicados DESPUÉS de normalizar
        initial_count = len(consolidated_df)
        consolidated_df = consolidated_df.drop_duplicates(keep='first')
        duplicates_removed = initial_count - len(consolidated_df)
        
        if duplicates_removed > 0:
            logger.info(f"Duplicados eliminados: {duplicates_removed}")
        
        # ENRIQUECIMIENTO: Agregar descripciones
        logger.info("Iniciando enriquecimiento de datos con descripciones...")
        
        # Extraer diccionarios maestros de BD 67
        master_dicts = self._extract_master_dictionaries(connections_used)
        
        # Agregar descripciones de catálogos normativos
        consolidated_df = self._add_catalog_descriptions(consolidated_df)
        
        # Agregar descripciones de tablas maestras (CUPS y CIE-10)
        consolidated_df = self._add_master_descriptions(consolidated_df, master_dicts)
        
        logger.info(f"Enriquecimiento completado: {len(consolidated_df.columns)} columnas totales")
        
        execution_time = time.time() - start_time
        
        logger.info(f"Consolidación completada: {len(consolidated_df)} registros únicos en {execution_time:.2f}s")
        
        return QueryResult(
            data=consolidated_df.to_dict('records'),
            record_count=len(consolidated_df),
            connections_used=connections_used,
            execution_time=execution_time,
            columns=list(consolidated_df.columns)
        )
    
    def _rename_columns_to_standard(self, df: pd.DataFrame, connection_id: str) -> pd.DataFrame:
        """
        Renombra columnas de una conexión específica a nombres estandarizados.
        
        Args:
            df: DataFrame con nombres de columnas específicos de la conexión
            connection_id: ID de conexión (67, 38, 39, 82)
        
        Returns:
            DataFrame con columnas renombradas
        """
        mapping = self.mapper.get_column_name_mapping(connection_id)
        df_renamed = df.rename(columns=mapping)
        
        logger.debug(f"Conexión {connection_id}: Renombradas {len(mapping)} columnas")
        
        return df_renamed
    
    def _normalize_categorical_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica normalización a campos categóricos."""
        
        categorical_fields = [
            'finalidad_consulta',
            'causa_externa',
            'tipo_diagnostico_principal',
            'tipo_documento'
        ]
        
        if self.normativa == '2275':
            categorical_fields.extend([
                'modalidad_grupo_servicio_tec_sal',
                'grupo_servicios',
                'concepto_recaudo'
            ])
        
        for field in categorical_fields:
            if field in df.columns:
                logger.debug(f"Normalizando campo: {field}")
                df[field] = df[field].apply(
                    lambda x: self.normalizer.normalize_value(x, field, self.normativa)
                )
        
        return df
    
    def _extract_master_dictionaries(self, connections_used: List[str]) -> Dict[str, Dict[str, str]]:
        """
        Extrae diccionarios de tablas maestras desde conexión 67.
        
        Args:
            connections_used: Lista de conexiones usadas en la consulta
        
        Returns:
            Dict con dos diccionarios: 'diagnosticos' y 'tecnologias'
            {
                'diagnosticos': {codigo: nombre},
                'tecnologias': {cups: descripcion}
            }
        """
        master_dicts = {
            'diagnosticos': {},
            'tecnologias': {}
        }
        
        # Solo extraer si se usó conexión 67
        if '67' not in connections_used:
            logger.info("Conexión 67 no utilizada, diccionarios maestros no disponibles")
            return master_dicts
        
        try:
            session = db_connections.get_session('67')
            
            # Extraer diccionario de diagnósticos (CIE-10)
            diagnosticos_query = """
                SELECT codigo, nombre
                FROM ma_diagnosticos
                WHERE activo = 1
            """
            
            result = session.execute(text(diagnosticos_query))
            for row in result:
                master_dicts['diagnosticos'][row.codigo.strip()] = row.nombre.strip()
            
            logger.info(f"Diccionario diagnósticos: {len(master_dicts['diagnosticos'])} códigos CIE-10")
            
            # Extraer diccionario de tecnologías (CUPS)
            tecnologias_query = """
                SELECT cups, cups_descipcion
                FROM ma_tecnologias
                WHERE activo = 1
            """
            
            result = session.execute(text(tecnologias_query))
            for row in result:
                master_dicts['tecnologias'][row.cups.strip()] = row.cups_descipcion.strip()
            
            logger.info(f"Diccionario tecnologías: {len(master_dicts['tecnologias'])} códigos CUPS")
            
            session.close()
            
        except Exception as e:
            logger.error(f"Error extrayendo diccionarios maestros: {str(e)}")
            # No fallar la ejecución, continuar sin descripciones
        
        return master_dicts
    
    def _add_catalog_descriptions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrega columnas descriptivas para campos con catálogos normativos.
        
        Campos enriquecidos:
        - finalidad_consulta → finalidad_consulta_descripcion
        - causa_externa → causa_externa_descripcion
        - tipo_diagnostico_principal → tipo_diagnostico_principal_descripcion
        
        Args:
            df: DataFrame consolidado
        
        Returns:
            DataFrame con columnas descriptivas agregadas
        """
        catalog_mappings = {
            'finalidad_consulta': 'finalidad_consulta_descripcion',
            'causa_externa': 'causa_externa_descripcion',
            'tipo_diagnostico_principal': 'tipo_diagnostico_principal_descripcion'
        }
        
        for code_field, desc_field in catalog_mappings.items():
            if code_field in df.columns:
                # Obtener catálogo correspondiente
                catalog = CatalogNormalizer._get_catalog(code_field, self.normativa)
                
                if catalog:
                    # Mapear códigos a descripciones
                    df[desc_field] = df[code_field].map(catalog)
                    
                    # Contar valores sin descripción
                    missing_count = df[desc_field].isna().sum()
                    if missing_count > 0:
                        logger.warning(f"{code_field}: {missing_count} valores sin descripción en catálogo")
                    else:
                        logger.debug(f"{code_field}: Todas las descripciones mapeadas correctamente")
                else:
                    logger.warning(f"Catálogo no encontrado para {code_field}")
        
        return df
    
    def _add_master_descriptions(
        self,
        df: pd.DataFrame,
        master_dicts: Dict[str, Dict[str, str]]
    ) -> pd.DataFrame:
        """
        Agrega columnas descriptivas para códigos CUPS y CIE-10 usando diccionarios maestros.
        
        Campos enriquecidos:
        - codigo_consulta → codigo_consulta_descripcion
        - codigo_diagnostico_principal → codigo_diagnostico_principal_descripcion
        - codigo_diagnostico_relacionado_1 → codigo_diagnostico_relacionado_1_descripcion
        - codigo_diagnostico_relacionado_2 → codigo_diagnostico_relacionado_2_descripcion
        - codigo_diagnostico_relacionado_3 → codigo_diagnostico_relacionado_3_descripcion
        
        Args:
            df: DataFrame consolidado
            master_dicts: Diccionarios extraídos de BD 67
        
        Returns:
            DataFrame con columnas descriptivas agregadas
        """
        # Mapeo de campos de diagnósticos
        diagnostico_fields = [
            'codigo_diagnostico_principal',
            'codigo_diagnostico_relacionado_1',
            'codigo_diagnostico_relacionado_2',
            'codigo_diagnostico_relacionado_3'
        ]
        
        diagnosticos_dict = master_dicts.get('diagnosticos', {})
        
        if diagnosticos_dict:
            for field in diagnostico_fields:
                if field in df.columns:
                    desc_field = f"{field}_descripcion"
                    
                    # Aplicar mapeo, manteniendo vacío si no hay match
                    df[desc_field] = df[field].map(diagnosticos_dict)
                    
                    # Contar valores mapeados
                    mapped_count = df[desc_field].notna().sum()
                    total_count = df[field].notna().sum()
                    
                    if total_count > 0:
                        coverage = (mapped_count / total_count) * 100
                        logger.info(f"{field}: {mapped_count}/{total_count} códigos con descripción ({coverage:.1f}%)")
        else:
            logger.warning("Diccionario de diagnósticos no disponible, descripciones CIE-10 omitidas")
        
        # Mapeo de códigos CUPS (tecnologías)
        tecnologias_dict = master_dicts.get('tecnologias', {})
        
        if tecnologias_dict and 'codigo_consulta' in df.columns:
            df['codigo_consulta_descripcion'] = df['codigo_consulta'].map(tecnologias_dict)
            
            mapped_count = df['codigo_consulta_descripcion'].notna().sum()
            total_count = df['codigo_consulta'].notna().sum()
            
            if total_count > 0:
                coverage = (mapped_count / total_count) * 100
                logger.info(f"codigo_consulta: {mapped_count}/{total_count} códigos con descripción ({coverage:.1f}%)")
        else:
            logger.warning("Diccionario de tecnologías no disponible, descripciones CUPS omitidas")
        
        return df
    
    def export_to_csv(
        self,
        query_result: QueryResult,
        filename: str,
        output_dir: Path
    ) -> str:
        """
        Exporta resultado a CSV según especificación.
        
        Args:
            query_result: Resultado de la consulta
            filename: Nombre del archivo
            output_dir: Directorio de salida (Path object)
        
        Returns:
            str: ruta completa del archivo generado
        """
        df = pd.DataFrame(query_result.data)
        
        # Reordenar columnas: código seguido de descripción
        ordered_columns = self._reorder_columns_with_descriptions(df.columns.tolist())
        df = df[ordered_columns]
        
        # Asegurar que el directorio existe
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = output_dir / filename
        
        # Exportar con especificaciones: UTF-8 BOM, separador ;
        df.to_csv(
            filepath,
            sep=';',
            index=False,
            encoding='utf-8-sig',
            date_format='%Y-%m-%d',
            na_rep=''
        )
        
        logger.info(f"Archivo CSV generado: {filepath} ({len(df.columns)} columnas, {len(df)} registros)")
        return str(filepath)
    
    def _reorder_columns_with_descriptions(self, columns: List[str]) -> List[str]:
        """
        Reordena columnas para que descripción aparezca inmediatamente después del código.
        
        Patrón deseado:
        - codigo_consulta
        - codigo_consulta_descripcion
        - finalidad_consulta
        - finalidad_consulta_descripcion
        - ...
        
        Args:
            columns: Lista de nombres de columnas
        
        Returns:
            Lista reordenada de columnas
        """
        # Identificar pares código-descripción
        base_columns = []
        description_columns = {}
        
        for col in columns:
            if col.endswith('_descripcion'):
                base_col = col.replace('_descripcion', '')
                description_columns[base_col] = col
            else:
                base_columns.append(col)
        
        # Construir lista ordenada
        ordered = []
        for col in base_columns:
            ordered.append(col)
            # Si existe descripción, agregarla inmediatamente después
            if col in description_columns:
                ordered.append(description_columns[col])
        
        return ordered