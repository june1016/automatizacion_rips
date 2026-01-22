"""Catálogos normativos y normalización de valores categóricos."""
import logging
import pandas as pd
import numpy as np
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class CatalogNormalizer:
    """Normaliza y valida valores categóricos contra catálogos oficiales."""
    
    # Catálogos oficiales por normativa
    FINALIDAD_CONSULTA = {
        '3374': {
            '01': 'Atención del parto (puerperio)',
            '02': 'Atención del recién nacido',
            '03': 'Atención en planificación familiar',
            '04': 'Detección de alteraciones de crecimiento y desarrollo del menor de diez años',
            '05': 'Detección de alteración del desarrollo joven',
            '06': 'Detección de alteraciones del embarazo',
            '07': 'Detección de alteraciones del adulto',
            '08': 'Detección de alteraciones de agudeza visual',
            '09': 'Detección de enfermedad profesional',
            '10': 'No aplica'
        },
        '2275': {
            '11': 'VALORACION INTEGRAL PARA LA PROMOCION Y MANTENIMIENTO',
            '12': 'DETECCION TEMPRANA DE ENFERMEDAD GENERAL',
            '13': 'DETECCION TEMPRANA DE ENFERMEDAD LABORAL',
            '14': 'PROTECCION ESPECIFICA',
            '15': 'DIAGNOSTICO',
            '16': 'TRATAMIENTO',
            '17': 'REHABILITACION',
            '18': 'PALIACION',
            '19': 'PLANIFICACION FAMILIAR Y ANTICONCEPCION',
            '20': 'PROMOCION Y APOYO A LA LACTANCIA MATERNA',
            '21': 'ATENCION BASICA DE ORIENTACION FAMILIAR',
            '22': 'ATENCION PARA EL CUIDADO PRECONCEPCIONAL',
            '23': 'ATENCION PARA EL CUIDADO PRENATAL',
            '24': 'INTERRUPCION VOLUNTARIA DEL EMBARAZO',
            '25': 'ATENCION DEL PARTO Y PUERPERIO',
            '26': 'ATENCION PARA EL CUIDADO DEL RECIEN NACIDO',
            '27': 'ATENCION PARA EL SEGUIMIENTO DEL RECIEN NACIDO',
            '28': 'PREPARACION PARA LA MATERNIDAD Y LA PATERNIDAD',
            '29': 'PROMOCION DE ACTIVIDAD FISICA',
            '30': 'PROMOCION DE LA CESACION DEL TABAQUISMO',
            '31': 'PREVENCION DEL CONSUMO DE SUSTANCIAS PSICOACTIVAS',
            '32': 'PROMOCION DE LA ALIMENTACION SALUDABLE',
            '33': 'PROMOCION PARA EL EJERCICIO DE LOS DERECHOS SEXUALES Y DERECHOS REPRODUCTIVOS',
            '34': 'PROMOCION PARA EL DESARROLLO DE HABILIDADES PARA LA VIDA',
            '35': 'PROMOCION PARA LA CONSTRUCCION DE ESTRATEGIAS DE AFRONTAMIENTO FRENTE A SUCESOS VITALES',
            '36': 'PROMOCION DE LA SANA CONVIVENCIA Y EL TEJIDO SOCIAL',
            '37': 'PROMOCION DE UN AMBIENTE SEGURO Y DE CUIDADO Y PROTECCION DEL AMBIENTE',
            '38': 'PROMOCION DEL EMPODERAMIENTO PARA EL EJERCICIO DEL DERECHO A LA SALUD',
            '39': 'PROMOCION PARA LA ADOPCION DE PRACTICAS DE CRIANZA Y CUIDADO PARA LA SALUD',
            '40': 'PROMOCION DE LA CAPACIDAD DE LA AGENCIA Y CUIDADO DE LA SALUD',
            '41': 'DESARROLLO DE HABILIDADES COGNITIVAS',
            '42': 'INTERVENCION COLECTIVA',
            '43': 'MODIFICACION DE LA ESTETICA CORPORAL FINES ESTETICOS',
            '44': 'OTRA'
        }
    }
    
    CAUSA_EXTERNA = {
        '3374': {
            '01': 'Accidente de trabajo',
            '02': 'Accidente de tránsito',
            '03': 'Accidente rábico',
            '04': 'Accidente ofídico',
            '05': 'Otro tipo de accidente',
            '06': 'Evento catastrófico',
            '07': 'Lesión por agresión',
            '08': 'Lesión auto infligida',
            '09': 'Sospecha de maltrato físico',
            '10': 'Sospecha de abuso sexual',
            '11': 'Sospecha de violencia sexual',
            '12': 'Sospecha de maltrato emocional',
            '13': 'Enfermedad general',
            '14': 'Enfermedad profesional',
            '15': 'Otra'
        },
        '2275': {
            '21': 'ACCIDENTE DE TRABAJO',
            '22': 'ACCIDENTE EN EL HOGAR',
            '23': 'ACCIDENTE DE TRANSITO DE ORIGEN COMUN',
            '24': 'ACCIDENTE DE TRANSITO DE ORIGEN LABORAL',
            '25': 'ACCIDENTE EN EL ENTORNO EDUCATIVO',
            '26': 'OTRO TIPO DE ACCIDENTE',
            '27': 'EVENTO CATASTROFICO DE ORIGEN NATURAL',
            '28': 'LESION POR AGRESION',
            '29': 'LESION AUTO INFLIGIDA',
            '30': 'SOSPECHA DE VIOLENCIA FISICA',
            '31': 'SOSPECHA DE VIOLENCIA PSICOLOGICA',
            '32': 'SOSPECHA DE VIOLENCIA SEXUAL',
            '33': 'SOSPECHA DE NEGLIGENCIA Y ABANDONO',
            '34': 'IVE RELACIONADO CON PELIGRO A LA SALUD O VIDA DE LA MUJER',
            '35': 'IVE POR MALFORMACION CONGENITA INCOMPATIBLE CON LA VIDA',
            '36': 'IVE POR VIOLENCIA SEXUAL, INCESTO O POR INSEMINACION ARTIFICIAL O TRANSFERENCIA DE OVULO FECUNDADO NO CONSENTIDA',
            '37': 'EVENTO ADVERSO EN SALUD',
            '38': 'ENFERMEDAD GENERAL',
            '39': 'ENFERMEDAD LABORAL',
            '40': 'PROMOCION Y MANTENIMIENTO DE LA SALUD ? INTERVENCIONES INDIVIDUALES',
            '41': 'INTERVENCION COLECTIVA',
            '42': 'ATENCION DE POBLACION MATERNO PERINATAL',
            '43': 'RIESGO AMBIENTAL',
            '44': 'OTROS EVENTOS CATASTROFICOS',
            '45': 'ACCIDENTE DE MINA ANTIPERSONAL ? MAP',
            '46': 'ACCIDENTE DE ARTEFACTO EXPLOSIVO IMPROVISADO ? AEI',
            '47': 'ACCIDENTE DE MUNICION SIN EXPLOTAR- MUSE',
            '48': 'OTRA VICTIMA DE CONFLICTO ARMADO COLOMBIANO',
            '49': 'IVE POR DECISION O MANIFESTACION DE VOLUNTAD DE LA PERSONA GESTANTE HASTA LA SEMANA 24 DE GESTACION'
        }
    }
    
    TIPO_DIAGNOSTICO_PRINCIPAL = {
        '3374': {
            '01': 'Impresión diagnóstica',
            '02': 'Confirmado nuevo',
            '03': 'Confirmado repetido'
        },
        '2275': {
            '01': 'Impresión diagnóstica',
            '02': 'Confirmado nuevo',
            '03': 'Confirmado repetido'
        }
    }
    
    MODALIDAD_GRUPO_SERVICIO = {
        '2275': {
            '1': 'Intramural',
            '2': 'Extramural unidad móvil',
            '3': 'Extramural domiciliaria',
            '4': 'Extramural jornada de salud',
            '6': 'Telemedicina interactiva',
            '7': 'Telemedicina no interactiva',
            '8': 'Telemedicina telexperticia',
            '9': 'Telemedicina telemonitoreo'
        }
    }
    
    GRUPO_SERVICIOS = {
        '2275': {
            '1': 'Consulta externa',
            '2': 'Apoyo diagnóstico y complementación terapéutica',
            '3': 'Internación',
            '4': 'Quirúrgico',
            '5': 'Atención inmediata'
        }
    }
    
    CONCEPTO_RECAUDO = {
        '2275': {
            '01': 'COPAGO',
            '02': 'CUOTA MODERADORA',
            '03': 'PAGOS COMPARTIDOS EN PLANES VOLUNTARIOS DE SALUD',
            '04': 'ANTICIPO',
            '05': 'NO APLICA'
        }
    }
    
    TIPO_DOCUMENTO = {
        'AS': 'Adulto sin identificacion',
        'CC': 'Cedula de Ciudadania',
        'CD': 'Carnet Diplomatico',
        'CE': 'Cedula de Extranjeria',
        'CN': 'Certificado de nacido vivo',
        'DE': 'Documento extranjero',
        'MS': 'Menor sin identificacion',
        'NI': 'Número de identificación tributario NIT',
        'NV': 'Certificado nacido vivo',
        'PA': 'Pasaporte',
        'PE': 'Permiso Especial de Permanencia',
        'PT': 'Permiso por protección temporal',
        'RC': 'Registro civil',
        'SC': 'Salvoconducto',
        'SI': 'Sin identificación',
        'TI': 'Tarjeta de Identidad',
        'NU': 'Número único de identificación'
    }
    
    @staticmethod
    def normalize_value(raw_value: any, field_name: str, normativa: str) -> str:
        """
        Normaliza valor categórico según reglas de negocio.
        
        Reglas:
        1. Detectar y manejar valores None/NaN/vacíos
        2. Trim espacios
        3. Pad con ceros a la izquierda según longitud esperada
        4. Validar contra catálogo oficial
        5. Si no existe → "VALOR DESCONOCIDO"
        """
        # CRÍTICO: Manejar NaN de pandas
        if pd.isna(raw_value):
            return 'VALOR DESCONOCIDO'
        
        # Manejar None explícito
        if raw_value is None:
            return 'VALOR DESCONOCIDO'
        
        # Convertir a string y limpiar
        value = str(raw_value).strip()
        
        # Manejar string vacío o 'nan' literal
        if value == '' or value.lower() == 'nan':
            return 'VALOR DESCONOCIDO'
        
        # Obtener catálogo correspondiente
        catalog = CatalogNormalizer._get_catalog(field_name, normativa)
        
        if catalog is None:
            logger.error(f"Catálogo no encontrado para {field_name} en normativa {normativa}")
            return value  # Retornar sin normalizar si no hay catálogo
        
        # Normalizar según tipo de campo
        normalized = CatalogNormalizer._normalize_by_field_type(value, field_name, catalog)
        
        # Validar contra catálogo
        if normalized in catalog:
            return normalized
        else:
            # Solo log si es un valor real (no desconocido)
            if value not in ['', 'nan', 'None', 'NULL']:
                logger.debug(f"Valor '{value}' no encontrado en catálogo {field_name}")
            return 'VALOR DESCONOCIDO'
    
    @staticmethod
    def _get_catalog(field_name: str, normativa: str) -> Optional[Dict[str, str]]:
        """Obtiene catálogo según campo y normativa."""
        
        catalog_map = {
            'finalidad_consulta': CatalogNormalizer.FINALIDAD_CONSULTA,
            'causa_externa': CatalogNormalizer.CAUSA_EXTERNA,
            'tipo_diagnostico_principal': CatalogNormalizer.TIPO_DIAGNOSTICO_PRINCIPAL,
            'modalidad_grupo_servicio_tec_sal': CatalogNormalizer.MODALIDAD_GRUPO_SERVICIO,
            'grupo_servicios': CatalogNormalizer.GRUPO_SERVICIOS,
            'concepto_recaudo': CatalogNormalizer.CONCEPTO_RECAUDO
        }
        
        # tipo_documento es global (sin normativa)
        if field_name == 'tipo_documento':
            return CatalogNormalizer.TIPO_DOCUMENTO
        
        # Resto de catálogos por normativa
        if field_name in catalog_map:
            catalog_dict = catalog_map[field_name]
            return catalog_dict.get(normativa)
        
        return None
    
    @staticmethod
    def _normalize_by_field_type(value: str, field_name: str, catalog: Dict[str, str]) -> str:
        """Normaliza valor según tipo de campo y catálogo."""
        
        # tipo_documento: uppercase, sin padding
        if field_name == 'tipo_documento':
            return value.upper()
        
        # modalidad_grupo_servicio y grupo_servicios: sin padding (1 dígito)
        if field_name in ['modalidad_grupo_servicio_tec_sal', 'grupo_servicios']:
            return value
        
        # Resto: padding a 2 dígitos si es numérico
        if value.isdigit():
            # Detectar longitud esperada del catálogo
            expected_length = len(next(iter(catalog.keys())))
            return value.zfill(expected_length)
        
        return value
    
    @staticmethod
    def get_catalog_options(field_name: str, normativa: str) -> list:
        """Obtiene lista de opciones para dropdown en UI."""
        catalog = CatalogNormalizer._get_catalog(field_name, normativa)
        
        if catalog is None:
            return []
        
        # Retornar lista de tuplas (código, descripción)
        return [(code, desc) for code, desc in catalog.items()]