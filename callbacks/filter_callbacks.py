"""Callbacks para manejo de filtros, consolidación de valores y UI interactiva."""

import logging
import base64
import tempfile
import os
from typing import Optional, List, Tuple

from dash import callback, Input, Output, State, html, MATCH, ctx, no_update, ALL

from utils.file_handler import FileHandler, ValueListParser
from utils.validators import ValueValidator

logger = logging.getLogger(__name__)


class FilterValueConsolidator:
    """Consolidador de valores de filtros desde lista o archivo."""

    @staticmethod
    def consolidate_multiple_values(
        mode: str,
        lista_value: Optional[str],
        archivo_content: Optional[str],
        archivo_filename: Optional[str],
        filter_type: Optional[str] = None,
    ) -> Tuple[bool, Optional[List[str]], Optional[str], Optional[str]]:
        """
        Consolida valores desde lista o archivo.

        Args:
            mode: Modo de entrada ('lista', 'archivo')
            lista_value: Valor del textarea de lista
            archivo_content: Contenido del archivo cargado (base64)
            archivo_filename: Nombre del archivo cargado
            filter_type: Tipo de filtro para validación específica

        Returns:
            Tupla (success, values, error_message, warning_message)
        """
        try:
            if mode == "lista":
                return FilterValueConsolidator._process_lista_mode(
                    lista_value, filter_type
                )

            elif mode == "archivo":
                return FilterValueConsolidator._process_archivo_mode(
                    archivo_content, archivo_filename, filter_type
                )

            else:
                return False, None, f"Modo desconocido: {mode}", None

        except Exception as e:
            logger.error(f"Error consolidando valores: {str(e)}")
            return False, None, f"Error procesando valores: {str(e)}", None

    @staticmethod
    def _validate_filter_specific(
        values: List[str], filter_type: Optional[str]
    ) -> Tuple[bool, List[str], Optional[str]]:
        """Aplica validación específica según tipo de filtro."""
        if filter_type == "codigo_prestador":
            from utils.validators import CodigoPrestadorValidator

            return CodigoPrestadorValidator.validate(values)

        return True, values, None

    @staticmethod
    def _process_lista_mode(
        text: Optional[str], filter_type: Optional[str] = None
    ) -> Tuple[bool, Optional[List[str]], Optional[str], Optional[str]]:
        """Procesa entrada de lista."""
        if not text or text.strip() == "":
            return True, [], None, None

        values = ValueListParser.parse_from_text(text)

        is_valid, validated_values, error = (
            FilterValueConsolidator._validate_filter_specific(values, filter_type)
        )

        if not is_valid:
            return False, None, error, None

        is_valid, error = ValueValidator.validate_multiple_values(
            validated_values, "lista"
        )

        if not is_valid:
            return False, None, error, None

        logger.info(f"Modo lista: {len(validated_values)} valores procesados")
        return True, validated_values, None, None

    @staticmethod
    def _process_archivo_mode(
        content: Optional[str],
        filename: Optional[str],
        filter_type: Optional[str] = None,
    ) -> Tuple[bool, Optional[List[str]], Optional[str], Optional[str]]:
        """Procesa archivo cargado con validación específica."""
        if not content or not filename:
            return True, [], None, None

        try:
            # Bloqueo Excel para código prestador
            if filter_type == "codigo_prestador" and filename.lower().endswith(
                (".xlsx", ".xls")
            ):
                error_msg = (
                    "Archivos Excel no permitidos para Código Prestador. "
                    "Excel elimina ceros iniciales. Use CSV o TXT."
                )
                return False, None, error_msg, None

            content_type, content_string = content.split(",")
            decoded = base64.b64decode(content_string)

            temp_dir = tempfile.gettempdir()
            temp_filepath = os.path.join(temp_dir, filename)

            logger.info(f"Guardando archivo temporal: {temp_filepath}")

            with open(temp_filepath, "wb") as f:
                f.write(decoded)

            success, values, error = FileHandler.read_values_from_file(temp_filepath)

            try:
                os.remove(temp_filepath)
            except:
                pass

            if not success:
                return False, None, error, None

            is_valid, validated_values, error = (
                FilterValueConsolidator._validate_filter_specific(values, filter_type)
            )

            if not is_valid:
                return False, None, error, None

            is_valid, error = ValueValidator.validate_multiple_values(
                validated_values, "archivo"
            )

            if not is_valid:
                return False, None, error, None

            logger.info(
                f"Archivo procesado: {len(validated_values)} valores desde {filename}"
            )
            return True, validated_values, None, None

        except Exception as e:
            logger.error(f"Error procesando archivo: {str(e)}")
            return False, None, f"Error procesando archivo: {str(e)}", None


# ==================== CALLBACK: CONSOLIDACIÓN DE FILTROS ====================


@callback(
    [
        Output({"type": MATCH, "rips": MATCH, "subtype": "values"}, "data"),
        Output({"type": MATCH, "rips": MATCH, "subtype": "count"}, "children"),
    ],
    [
        Input({"type": MATCH, "rips": MATCH, "subtype": "mode"}, "value"),
        Input({"type": MATCH, "rips": MATCH, "subtype": "lista"}, "value"),
        Input({"type": MATCH, "rips": MATCH, "subtype": "archivo"}, "contents"),
    ],
    State({"type": MATCH, "rips": MATCH, "subtype": "archivo"}, "filename"),
    prevent_initial_call=True,
)
def consolidate_filter_values(mode, lista, archivo_content, archivo_filename):
    """
    Consolida valores de filtros con entrada múltiple.

    Maneja todos los filtros con múltiples valores usando Pattern-Matching:
    - filter-codigo-prestador (validación específica + bloqueo Excel)
    - filter-documento-usuario
    - filter-diagnostico-principal
    - filter-diagnostico-relacionado-1/2/3
    """
    if mode is None:
        return [], html.Small("0 valores", className="text-muted")

    # Identificar tipo de filtro
    filter_type = None
    if ctx.triggered_id:
        triggered_type = ctx.triggered_id.get("type", "")
        if "filter-codigo-prestador" in triggered_type:
            filter_type = "codigo_prestador"

    success, values, error, warning = (
        FilterValueConsolidator.consolidate_multiple_values(
            mode, lista, archivo_content, archivo_filename, filter_type
        )
    )

    if not success:
        return [], html.Small(error, className="text-danger")

    count = len(values) if values else 0

    if count == 0:
        return [], html.Small("0 valores", className="text-muted")

    if warning:
        return values, html.Div(
            [
                html.Small(f"✓ {count} valores cargados", className="text-success"),
                html.Br(),
                html.Small(
                    warning, className="text-warning", style={"fontSize": "0.85em"}
                ),
            ]
        )

    return values, html.Small(f"✓ {count} valores cargados", className="text-success")


# ==================== CALLBACK: SELECCIONAR TODAS LAS COLUMNAS ====================


@callback(
    Output({"type": "checklist-columns", "rips": MATCH}, "value"),
    Input({"type": "btn-select-all-columns", "rips": MATCH}, "n_clicks"),
    State({"type": "checklist-columns", "rips": MATCH}, "options"),
    prevent_initial_call=True,
)
def select_all_columns(n_clicks, options):
    """Selecciona todas las columnas disponibles del checklist."""
    if not n_clicks or not options:
        return []

    all_values = [opt["value"] for opt in options]
    logger.info(f"Seleccionadas {len(all_values)} columnas")

    return all_values


# ==================== CALLBACK: TOGGLE DIAGNÓSTICOS RELACIONADOS ====================


@callback(
    [
        Output("collapse-diag-relacionados", "is_open"),
        Output("icon-diag-relacionados", "className"),
    ],
    Input("btn-toggle-diag-relacionados", "n_clicks"),
    State("collapse-diag-relacionados", "is_open"),
    prevent_initial_call=True,
)
def toggle_diagnosticos_relacionados(n_clicks, is_open):
    """Alterna visibilidad de diagnósticos relacionados."""
    if not n_clicks:
        return no_update, no_update

    new_state = not is_open
    icon = "bi bi-dash-circle me-2" if new_state else "bi bi-plus-circle me-2"

    logger.info(f"Diagnósticos relacionados: {'abierto' if new_state else 'cerrado'}")
    return new_state, icon


# ==================== CALLBACK: ABRIR MODAL DIAGNÓSTICOS (BOTÓN EXPLÍCITO) ====================


@callback(
    [Output("modal-diagnosticos", "is_open"), Output("modal-diag-count", "children")],
    [
        Input("btn-apply-diag-all", "n_clicks"),
        Input("modal-diag-only-principal", "n_clicks"),
        Input("modal-diag-all", "n_clicks"),
    ],
    State(
        {"type": "filter-diagnostico-principal", "rips": ALL, "subtype": "values"},
        "data",
    ),
    prevent_initial_call=True,
)
def toggle_modal_diagnosticos(btn_open, btn_only, btn_all, all_diag_principal):
    """
    Abre modal SOLO cuando usuario hace clic en botón explícito.

    Botón: "Aplicar a todos los diagnósticos relacionados"
    NO se abre automáticamente al cargar valores.
    """
    triggered = ctx.triggered_id

    logger.info(f"Modal diagnósticos trigger: {triggered}")

    # Cerrar modal si usuario hizo clic en botones del modal
    if triggered in ["modal-diag-only-principal", "modal-diag-all"]:
        logger.info("Cerrando modal (botón de acción)")
        return False, ""

    # Abrir modal si usuario hizo clic en botón explícito
    if triggered == "btn-apply-diag-all":
        # Verificar que hay valores en diagnóstico principal
        if all_diag_principal and len(all_diag_principal) > 0:
            values = all_diag_principal[0]
            if values and len(values) > 0:
                count_text = f"{len(values)} códigos"
                logger.info(f"Abriendo modal: {count_text}")
                return True, count_text

    return False, ""


# ==================== CALLBACK: COPIAR DIAGNÓSTICOS A TODOS LOS CAMPOS ====================


@callback(
    [
        Output(
            {
                "type": "filter-diagnostico-relacionado-1",
                "rips": "AC",
                "subtype": "lista",
            },
            "value",
        ),
        Output(
            {
                "type": "filter-diagnostico-relacionado-2",
                "rips": "AC",
                "subtype": "lista",
            },
            "value",
        ),
        Output(
            {
                "type": "filter-diagnostico-relacionado-3",
                "rips": "AC",
                "subtype": "lista",
            },
            "value",
        ),
        Output(
            {
                "type": "filter-diagnostico-relacionado-1",
                "rips": "AC",
                "subtype": "mode",
            },
            "value",
        ),
        Output(
            {
                "type": "filter-diagnostico-relacionado-2",
                "rips": "AC",
                "subtype": "mode",
            },
            "value",
        ),
        Output(
            {
                "type": "filter-diagnostico-relacionado-3",
                "rips": "AC",
                "subtype": "mode",
            },
            "value",
        ),
    ],
    Input("modal-diag-all", "n_clicks"),
    State(
        {"type": "filter-diagnostico-principal", "rips": "AC", "subtype": "lista"},
        "value",
    ),
    prevent_initial_call=True,
)
def copy_diagnosticos_to_all(n_clicks, diag_principal_text):
    """
    Copia diagnósticos del principal a todos los relacionados.

    Se activa SOLO cuando usuario hace clic en "Sí, copiar a todos" en el modal.
    """
    if not n_clicks:
        logger.info("copy_diagnosticos_to_all: n_clicks es None")
        return no_update, no_update, no_update, no_update, no_update, no_update

    if not diag_principal_text or diag_principal_text.strip() == "":
        logger.warning("copy_diagnosticos_to_all: Sin texto en diagnóstico principal")
        return "", "", "", "lista", "lista", "lista"

    # Copiar el mismo texto a todos los campos relacionados
    logger.info(
        f"Copiando diagnósticos a campos relacionados: {len(diag_principal_text)} caracteres"
    )

    # Cambiar modo a 'lista' para que se active el campo de texto
    return (
        diag_principal_text,  # Relacionado 1
        diag_principal_text,  # Relacionado 2
        diag_principal_text,  # Relacionado 3
        "lista",  # Modo relacionado 1
        "lista",  # Modo relacionado 2
        "lista",  # Modo relacionado 3
    )
