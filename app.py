"""Aplicación principal - Sistema de Automatización RIPS."""

import logging
import os
from dash import (
    Dash,
    html,
    dcc,
    Input,
    Output,
    State,
    callback,
    ctx,
    no_update,
    ALL,
    MATCH,
)
import dash_bootstrap_components as dbc
from datetime import datetime
from config.settings import app_config
from views.layout import AppLayout, StepContent, ACStepContent
from views.components import GlobalFiltersPanel, QuerySummary
from views.ac_view import ACFiltersPanel, ACColumnsPanel, ACResultsPanel, ACActionsPanel
from controllers.ac_controller import ACController
from models.base import DateRange, GlobalFilters
from models.ac_model import ACSpecificFilters
from utils.validators import DateValidator
from callbacks import filter_callbacks  # noqa: F401


# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Inicializar aplicación Dash
app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css",
    ],
    suppress_callback_exceptions=True,
)

app.title = "Sistema RIPS - Savia Salud"
app.layout = AppLayout.create_layout()


# ==================== CALLBACKS DE NAVEGACIÓN ====================


@callback(
    [
        Output("app-state", "data"),
        Output("progress-container", "children"),
        Output("main-content", "children"),
        Output("navigation-footer", "children"),
    ],
    [Input("btn-forward", "n_clicks"), Input("btn-back", "n_clicks")],
    State("app-state", "data"),
    prevent_initial_call=False,
)
def handle_navigation(btn_forward_clicks, btn_back_clicks, state):
    """Maneja navegación entre pasos."""
    triggered_id = ctx.triggered_id
    current_step = state.get("current_step", 0)

    if current_step == 5 and triggered_id == "btn-forward":
        state["current_step"] = 0
        state["query_result"] = None
        current_step = 0

    elif triggered_id == "btn-forward":
        can_advance, error_message = _validate_current_step(state)

        if not can_advance:
            logger.warning(
                f"No se puede avanzar desde paso {current_step}: {error_message}"
            )
            return (
                state,
                AppLayout._create_stepper(current_step),
                _render_step_content(current_step, state),
                _render_navigation_footer(current_step),
            )

        if current_step < 3:
            current_step = min(current_step + 1, 3)
            state["current_step"] = current_step

    elif triggered_id == "btn-back":
        if current_step > 0 and current_step != 5:
            current_step = max(current_step - 1, 0)
            state["current_step"] = current_step

    logger.info(f"Navegación: paso {current_step}")

    return (
        state,
        AppLayout._create_stepper(current_step),
        _render_step_content(current_step, state),
        _render_navigation_footer(current_step),
    )


@callback(
    Output("app-state", "data", allow_duplicate=True),
    Input("radio-normativa", "value"),
    State("app-state", "data"),
    prevent_initial_call=True,
)
def update_normativa_in_state(normativa, state):
    """Actualiza normativa seleccionada."""
    if normativa:
        state["normativa"] = normativa
        logger.info(f"Normativa: {normativa}")
    return state


@callback(
    Output("app-state", "data", allow_duplicate=True),
    Input("radio-tipos-rips", "value"),
    State("app-state", "data"),
    prevent_initial_call=True,
)
def update_tipos_rips_in_state(tipo_rips, state):
    """Actualiza tipo RIPS seleccionado."""
    state["tipo_rips"] = tipo_rips
    logger.info(f"Tipo RIPS: {tipo_rips}")
    return state


# ==================== CALLBACKS DE LOADING CON STORE INTERMEDIO ====================


@callback(
    Output("loading-trigger", "data"),
    Input("app-state", "data"),
    prevent_initial_call=True,
)
def update_loading_trigger(state):
    """
    Actualiza trigger para activar/desactivar loading.

    Este callback Python solo actualiza el Store.
    El clientside callback JavaScript lee el Store y actúa.
    """
    current_step = state.get("current_step", 0)

    # Generar timestamp único para forzar cambio
    import time

    timestamp = int(time.time() * 1000)

    trigger_data = {
        "show": current_step == 3,
        "step": current_step,
        "timestamp": timestamp,
    }

    logger.info(f"Loading trigger actualizado: {trigger_data}")

    return trigger_data


app.clientside_callback(
    """
    function(triggerData) {
        // console.log('🔔 Loading trigger recibido:', triggerData);
        const show = triggerData.show;
        const step = triggerData.step;
        // Esperar a que dashLoadingSystem esté disponible
        const waitForSystem = function(callback) {
            if (window.dashLoadingSystem) {
                callback();
            } else {
                console.log('⏳ Esperando dashLoadingSystem...');
                setTimeout(function() {
                    waitForSystem(callback);
                }, 50);
            }
        };
        waitForSystem(function() {
            if (show && step === 3) {
                // console.log('📊 Activando loading para Paso 3');
                window.dashLoadingSystem.showForStep3();
            } else if (!show && step !== 3) {
                // console.log('🚪 Desactivando loading (no es Paso 3)');
                window.dashLoadingSystem.hide();
            }
        });
        return window.dash_clientside.no_update;
    }
    """,
    Output("loading-trigger", "data", allow_duplicate=True),
    Input("loading-trigger", "data"),
    prevent_initial_call=True,
)

# ==================== CALLBACK DE LOADING OVERLAY (QUERY) ====================


@callback(
    Output("loading-overlay", "style"),
    Input("app-state", "data"),
    prevent_initial_call=True,
)
def toggle_loading_overlay(state):
    """Muestra overlay durante ejecución de query."""
    if state.get("query_processing"):
        return {"display": "flex"}
    return {"display": "none"}


# ==================== FUNCIONES AUXILIARES ====================


def _validate_current_step(state: dict) -> tuple[bool, str]:
    """Valida si se puede avanzar desde paso actual."""
    current_step = state.get("current_step", 0)

    if current_step == 0:
        return True, ""

    elif current_step == 1:
        if not state.get("normativa"):
            return False, "Debe seleccionar una normativa"
        return True, ""

    elif current_step == 2:
        if not state.get("tipo_rips"):
            return False, "Debe seleccionar un tipo de RIPS"
        return True, ""

    elif current_step == 3:
        return True, ""

    return True, ""


def _render_step_content(step: int, state: dict):
    """Renderiza contenido del paso actual."""
    if step == 0:
        return StepContent.step_0_inicio()

    elif step == 1:
        return StepContent.step_1_normativa(state.get("normativa"))

    elif step == 2:
        return StepContent.step_2_tipos_rips(state.get("tipo_rips"))

    elif step == 3:
        normativa = state.get("normativa")
        tipo = state.get("tipo_rips")

        if tipo == "AC":
            return ACStepContent.step_3_configuracion_ac(normativa)

        return html.Div("Configuración no disponible")

    elif step == 5:
        query_result = state.get("query_result")
        if query_result:
            return ACResultsPanel.create(query_result)
        return html.Div("No hay resultados disponibles")

    return html.Div("Paso no implementado")


def _render_navigation_footer(step: int):
    """Renderiza footer de navegación."""
    can_go_back = step > 0 and step != 5
    can_go_forward = step < 3
    forward_label = "Siguiente"

    if step == 3:
        can_go_forward = False
        forward_label = ""
    elif step == 5:
        forward_label = "Nueva Consulta"
        can_go_back = False
        can_go_forward = True

    return AppLayout._create_navigation_footer(
        current_step=step,
        can_go_back=can_go_back,
        can_go_forward=can_go_forward,
        forward_label=forward_label,
    )


def _toggle_input_mode(mode: str):
    """Alterna visibilidad de modos de entrada."""
    lista_style = {"display": "block" if mode == "lista" else "none"}
    archivo_style = {"display": "block" if mode == "archivo" else "none"}
    return lista_style, archivo_style


# ==================== CALLBACKS DE PASO 3 (CONFIGURACIÓN) ====================


@callback(
    Output("panel-filtros-globales", "children"),
    Input("app-state", "data"),
)
def render_global_filters(state):
    """Renderiza panel de filtros globales."""
    if state.get("current_step") != 3:
        return html.Div()

    normativa = state.get("normativa")
    tipo = state.get("tipo_rips")

    if tipo == "AC":
        return GlobalFiltersPanel.create(normativa, rips_type="AC")

    return html.Div()


@callback(
    Output("panel-filtros-especificos", "children"),
    Input("app-state", "data"),
)
def render_specific_filters(state):
    """Renderiza panel de filtros específicos."""
    if state.get("current_step") != 3:
        return html.Div()

    normativa = state.get("normativa")
    tipo = state.get("tipo_rips")

    if tipo == "AC":
        return ACFiltersPanel.create(normativa, rips_type="AC")

    return html.Div("Filtros específicos no disponibles")


@callback(
    Output("panel-columnas", "children"),
    Input("app-state", "data"),
)
def render_columns_panel(state):
    """Renderiza panel de selección de columnas."""
    if state.get("current_step") != 3:
        return html.Div()

    normativa = state.get("normativa")
    tipo = state.get("tipo_rips")

    if tipo == "AC":
        return ACColumnsPanel.create(normativa, rips_type="AC")

    return html.Div("Columnas no disponibles")


@callback(
    Output("panel-acciones", "children"),
    Input("app-state", "data"),
)
def render_actions_panel(state):
    """Renderiza panel de acciones."""
    if state.get("current_step") != 3:
        return html.Div()

    tipo = state.get("tipo_rips")

    if tipo == "AC":
        return ACActionsPanel.create(rips_type="AC")

    return html.Div()


@callback(
    Output("panel-resumen", "children"),
    [
        Input("app-state", "data"),
        Input({"type": "date-picker-start", "rips": ALL}, "date"),
        Input({"type": "date-picker-end", "rips": ALL}, "date"),
        Input({"type": "checklist-columns", "rips": ALL}, "value"),
        Input({"type": "filter-finalidad-consulta", "rips": ALL}, "value"),
        Input({"type": "filter-causa-externa", "rips": ALL}, "value"),
        Input({"type": "filter-tipo-diagnostico-principal", "rips": ALL}, "value"),
        Input(
            {"type": "filter-diagnostico-principal", "rips": ALL, "subtype": "values"},
            "data",
        ),
        Input(
            {
                "type": "filter-diagnostico-relacionado-1",
                "rips": ALL,
                "subtype": "values",
            },
            "data",
        ),
        Input(
            {
                "type": "filter-diagnostico-relacionado-2",
                "rips": ALL,
                "subtype": "values",
            },
            "data",
        ),
        Input(
            {
                "type": "filter-diagnostico-relacionado-3",
                "rips": ALL,
                "subtype": "values",
            },
            "data",
        ),
        Input(
            {"type": "filter-valor-consulta", "rips": ALL, "subtype": "min"}, "value"
        ),
        Input(
            {"type": "filter-valor-consulta", "rips": ALL, "subtype": "max"}, "value"
        ),
        Input(
            {"type": "filter-codigo-prestador", "rips": ALL, "subtype": "values"},
            "data",
        ),
        Input(
            {"type": "filter-documento-usuario", "rips": ALL, "subtype": "values"},
            "data",
        ),
    ],
)
def render_summary_panel(
    state,
    all_dates_start,
    all_dates_end,
    all_selected_columns,
    all_finalidad,
    all_causa_externa,
    all_tipo_diag,
    all_diag_principal,
    all_diag_rel1,
    all_diag_rel2,
    all_diag_rel3,
    all_valor_min,
    all_valor_max,
    all_cod_prestador,
    all_doc_usuario,
):
    """Renderiza panel de resumen."""
    if state.get("current_step") != 3:
        return html.Div()

    fecha_inicio = all_dates_start[0] if all_dates_start else None
    fecha_fin = all_dates_end[0] if all_dates_end else None
    selected_columns = all_selected_columns[0] if all_selected_columns else []
    finalidad = all_finalidad[0] if all_finalidad else None
    causa_externa = all_causa_externa[0] if all_causa_externa else None
    tipo_diag = all_tipo_diag[0] if all_tipo_diag else None
    diag_principal = all_diag_principal[0] if all_diag_principal else []
    diag_rel1 = all_diag_rel1[0] if all_diag_rel1 else []
    diag_rel2 = all_diag_rel2[0] if all_diag_rel2 else []
    diag_rel3 = all_diag_rel3[0] if all_diag_rel3 else []
    valor_min = all_valor_min[0] if all_valor_min else None
    valor_max = all_valor_max[0] if all_valor_max else None
    cod_prestador = all_cod_prestador[0] if all_cod_prestador else []
    doc_usuario = all_doc_usuario[0] if all_doc_usuario else []

    if fecha_inicio is None or fecha_fin is None:
        return html.Div()

    num_filtros_globales = 1
    if cod_prestador:
        num_filtros_globales += 1
    if doc_usuario:
        num_filtros_globales += 1

    num_filtros_especificos = sum(
        [
            bool(finalidad),
            bool(causa_externa),
            bool(tipo_diag),
            bool(diag_principal),
            bool(diag_rel1),
            bool(diag_rel2),
            bool(diag_rel3),
            bool(valor_min is not None or valor_max is not None),
        ]
    )

    summary_data = {
        "normativa": state.get("normativa", "No seleccionada"),
        "tipo": state.get("tipo_rips", "No seleccionado"),
        "fecha_inicio": fecha_inicio or "",
        "fecha_fin": fecha_fin or "",
        "num_filtros_globales": num_filtros_globales,
        "num_filtros_especificos": num_filtros_especificos,
        "num_columnas": len(selected_columns) if selected_columns else 0,
        "is_valid": True,
    }

    return QuerySummary.create(summary_data)


# ==================== CALLBACKS DE TOGGLE ====================


@callback(
    [
        Output({"type": MATCH, "rips": MATCH, "subtype": "lista-container"}, "style"),
        Output({"type": MATCH, "rips": MATCH, "subtype": "archivo-container"}, "style"),
    ],
    Input({"type": MATCH, "rips": MATCH, "subtype": "mode"}, "value"),
)
def toggle_input_mode(mode):
    """Alterna modo de entrada."""
    if not mode:
        return {"display": "none"}, {"display": "none"}
    return _toggle_input_mode(mode)


# ==================== CALLBACKS DE VALIDACIÓN ====================


@callback(
    Output({"type": "date-validation-feedback", "rips": MATCH}, "children"),
    [
        Input({"type": "date-picker-start", "rips": MATCH}, "date"),
        Input({"type": "date-picker-end", "rips": MATCH}, "date"),
    ],
    State("app-state", "data"),
)
def validate_date_range(start_date_str, end_date_str, state):
    """Valida rango de fechas."""
    if state.get("current_step") != 3:
        return html.Div()

    if not start_date_str or not end_date_str:
        return html.Div()

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

        is_valid, error_message = DateValidator.validate_range(start_date, end_date)

        if not is_valid:
            return dbc.Alert(
                error_message, color="danger", className="alert-savia mb-0 py-2"
            )

        date_range = DateRange(start_date, end_date)
        connections = date_range.get_connections()

        return dbc.Alert(
            [
                html.I(className="bi bi-check-circle-fill me-2"),
                f"Rango válido. Conexiones: {', '.join(connections)}",
            ],
            color="success",
            className="alert-savia mb-0 py-2",
        )

    except Exception as e:
        logger.error(f"Error validando fechas: {str(e)}")
        return dbc.Alert(
            "Error al validar fechas", color="danger", className="alert-savia mb-0 py-2"
        )


# ==================== CALLBACK DE EJECUCIÓN ====================


@callback(
    [
        Output("results-container", "children"),
        Output("app-state", "data", allow_duplicate=True),
        Output("progress-container", "children", allow_duplicate=True),
        Output("navigation-footer", "children", allow_duplicate=True),
        Output("main-content", "style"),
    ],
    Input({"type": "btn-generar-reporte", "rips": "AC"}, "n_clicks"),
    [
        State("app-state", "data"),
        State({"type": "date-picker-start", "rips": ALL}, "date"),
        State({"type": "date-picker-end", "rips": ALL}, "date"),
        State({"type": "checklist-columns", "rips": ALL}, "value"),
        State(
            {"type": "filter-codigo-prestador", "rips": ALL, "subtype": "values"},
            "data",
        ),
        State(
            {"type": "filter-documento-usuario", "rips": ALL, "subtype": "values"},
            "data",
        ),
        State({"type": "filter-finalidad-consulta", "rips": ALL}, "value"),
        State({"type": "filter-causa-externa", "rips": ALL}, "value"),
        State({"type": "filter-tipo-diagnostico-principal", "rips": ALL}, "value"),
        State(
            {"type": "filter-diagnostico-principal", "rips": ALL, "subtype": "values"},
            "data",
        ),
        State(
            {
                "type": "filter-diagnostico-relacionado-1",
                "rips": ALL,
                "subtype": "values",
            },
            "data",
        ),
        State(
            {
                "type": "filter-diagnostico-relacionado-2",
                "rips": ALL,
                "subtype": "values",
            },
            "data",
        ),
        State(
            {
                "type": "filter-diagnostico-relacionado-3",
                "rips": ALL,
                "subtype": "values",
            },
            "data",
        ),
        State(
            {"type": "filter-valor-consulta", "rips": ALL, "subtype": "min"}, "value"
        ),
        State(
            {"type": "filter-valor-consulta", "rips": ALL, "subtype": "max"}, "value"
        ),
    ],
    prevent_initial_call=True,
    running=[
        (
            Output({"type": "btn-generar-reporte", "rips": "AC"}, "disabled"),
            True,
            False,
        ),
        (
            Output({"type": "btn-generar-reporte", "rips": "AC"}, "children"),
            [
                dbc.Spinner(size="sm", spinnerClassName="spinner-savia"),
                " Procesando...",
            ],
            [html.I(className="bi bi-play-circle-fill me-2"), "Generar Reporte"],
        ),
        (Output("btn-back", "disabled"), True, False),
    ],
)
def execute_query(
    n_clicks,
    state,
    all_fecha_inicio,
    all_fecha_fin,
    all_selected_columns,
    all_codigo_prestador_values,
    all_documento_usuario_values,
    all_finalidad_consulta,
    all_causa_externa,
    all_tipo_diagnostico_principal,
    all_diag_principal_values,
    all_diag_rel_1_values,
    all_diag_rel_2_values,
    all_diag_rel_3_values,
    all_valor_consulta_min,
    all_valor_consulta_max,
):
    """Ejecuta consulta con logging exhaustivo."""
    logger.info("=" * 80)
    logger.info("🚀 CALLBACK EXECUTE_QUERY INICIADO")
    logger.info("=" * 80)

    if not n_clicks:
        logger.info("❌ n_clicks es None/0 - Ignorando")
        return html.Div(), state, no_update, no_update, {"pointerEvents": "auto"}

    logger.info(f"✓ n_clicks detectado: {n_clicks}")

    state["query_processing"] = True

    try:
        logger.info("\n📊 EXTRAYENDO VALORES DE LISTAS...")
        logger.info(f"  - all_fecha_inicio: {all_fecha_inicio}")
        logger.info(f"  - all_fecha_fin: {all_fecha_fin}")
        logger.info(
            f"  - all_selected_columns (len): {len(all_selected_columns) if all_selected_columns else 0}"
        )

        fecha_inicio = (
            all_fecha_inicio[0]
            if all_fecha_inicio and len(all_fecha_inicio) > 0
            else None
        )
        fecha_fin = (
            all_fecha_fin[0] if all_fecha_fin and len(all_fecha_fin) > 0 else None
        )

        logger.info(f"\n📅 FECHAS EXTRAÍDAS:")
        logger.info(f"  - fecha_inicio: {fecha_inicio}")
        logger.info(f"  - fecha_fin: {fecha_fin}")

        if not fecha_inicio or not fecha_fin:
            error_msg = "❌ Fechas no disponibles"
            logger.error(error_msg)
            state["query_processing"] = False
            error_panel = dbc.Alert(error_msg, color="danger", className="alert-savia")
            return error_panel, state, no_update, no_update, {"pointerEvents": "auto"}

        selected_columns = (
            all_selected_columns[0]
            if all_selected_columns and len(all_selected_columns) > 0
            else []
        )

        logger.info(f"\n📋 COLUMNAS:")
        logger.info(f"  - Cantidad: {len(selected_columns)}")
        logger.info(
            f"  - Columnas: {selected_columns[:5]}..."
            if len(selected_columns) > 5
            else f"  - Columnas: {selected_columns}"
        )

        if not selected_columns:
            error_msg = "❌ Debe seleccionar al menos 1 columna"
            logger.error(error_msg)
            state["query_processing"] = False
            error_panel = dbc.Alert(error_msg, color="danger", className="alert-savia")
            return error_panel, state, no_update, no_update, {"pointerEvents": "auto"}

        logger.info("\n🔍 EXTRAYENDO FILTROS...")

        codigo_prestador_values = (
            all_codigo_prestador_values[0] if all_codigo_prestador_values else []
        )
        documento_usuario_values = (
            all_documento_usuario_values[0] if all_documento_usuario_values else []
        )
        finalidad_consulta = (
            all_finalidad_consulta[0] if all_finalidad_consulta else None
        )
        causa_externa = all_causa_externa[0] if all_causa_externa else None
        tipo_diagnostico_principal = (
            all_tipo_diagnostico_principal[0]
            if all_tipo_diagnostico_principal
            else None
        )
        diag_principal_values = (
            all_diag_principal_values[0] if all_diag_principal_values else []
        )
        diag_rel_1_values = all_diag_rel_1_values[0] if all_diag_rel_1_values else []
        diag_rel_2_values = all_diag_rel_2_values[0] if all_diag_rel_2_values else []
        diag_rel_3_values = all_diag_rel_3_values[0] if all_diag_rel_3_values else []
        valor_consulta_min = (
            all_valor_consulta_min[0] if all_valor_consulta_min else None
        )
        valor_consulta_max = (
            all_valor_consulta_max[0] if all_valor_consulta_max else None
        )

        logger.info(f"  - Código prestador: {len(codigo_prestador_values)} valores")
        logger.info(f"  - Documento usuario: {len(documento_usuario_values)} valores")
        logger.info(f"  - Finalidad consulta: {finalidad_consulta}")
        logger.info(f"  - Causa externa: {causa_externa}")
        logger.info(f"  - Tipo diagnóstico: {tipo_diagnostico_principal}")
        logger.info(f"  - Diag principal: {len(diag_principal_values)} valores")
        logger.info(f"  - Valor min/max: {valor_consulta_min} / {valor_consulta_max}")

        logger.info("\n🔄 CONVIRTIENDO FECHAS...")
        start_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        end_date = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
        logger.info(f"  ✓ Fechas convertidas: {start_date} a {end_date}")

        logger.info("\n🏗️ CONSTRUYENDO FILTROS...")
        global_filters = GlobalFilters(
            date_range=DateRange(start_date, end_date),
            codigo_prestador=(
                codigo_prestador_values if codigo_prestador_values else None
            ),
            documento_usuario=(
                documento_usuario_values if documento_usuario_values else None
            ),
        )
        logger.info("  ✓ Filtros globales creados")

        specific_filters = ACSpecificFilters(
            finalidad_consulta=finalidad_consulta if finalidad_consulta else None,
            causa_externa=causa_externa if causa_externa else None,
            codigo_diagnostico_principal=(
                diag_principal_values if diag_principal_values else None
            ),
            codigo_diagnostico_relacionado_1=(
                diag_rel_1_values if diag_rel_1_values else None
            ),
            codigo_diagnostico_relacionado_2=(
                diag_rel_2_values if diag_rel_2_values else None
            ),
            codigo_diagnostico_relacionado_3=(
                diag_rel_3_values if diag_rel_3_values else None
            ),
            tipo_diagnostico_principal=(
                tipo_diagnostico_principal if tipo_diagnostico_principal else None
            ),
            valor_consulta_min=valor_consulta_min,
            valor_consulta_max=valor_consulta_max,
        )
        logger.info("  ✓ Filtros específicos creados")

        normativa = state.get("normativa")
        logger.info(f"\n🎯 INICIALIZANDO CONTROLLER...")
        logger.info(f"  - Normativa: {normativa}")

        controller = ACController(normativa)
        logger.info("  ✓ Controller inicializado")

        logger.info("\n⚡ EJECUTANDO CONSULTA EN BD...")

        result = controller.execute_query(
            global_filters=global_filters,
            specific_filters=specific_filters,
            columns=selected_columns,
            # estimate_before_execute=False,
        )

        logger.info(f"\n✅ CONSULTA COMPLETADA")
        logger.info(f"  - Success: {result.success}")
        logger.info(f"  - Message: {result.message}")
        logger.info(
            f"  - Records: {result.query_result.record_count if result.query_result else 0}"
        )
        logger.info(
            f"  - Time: {result.query_result.execution_time if result.query_result else 0}s"
        )

        state["query_result"] = {
            "success": result.success,
            "message": result.message,
            "record_count": (
                result.query_result.record_count if result.query_result else 0
            ),
            "execution_time": (
                result.query_result.execution_time if result.query_result else 0
            ),
            "connections_used": (
                result.query_result.connections_used if result.query_result else []
            ),
            "csv_filepath": result.csv_filepath,
            "filename": (
                os.path.basename(result.csv_filepath) if result.csv_filepath else ""
            ),
            "error_details": result.error_details,
        }

        state["current_step"] = 5
        state["query_processing"] = False

        results_panel = ACResultsPanel.create(state["query_result"])
        stepper = AppLayout._create_stepper(5)
        navigation = AppLayout._create_navigation_footer(
            current_step=5,
            can_go_back=False,
            can_go_forward=True,
            forward_label="Nueva Consulta",
        )

        logger.info("=" * 80)
        logger.info("🎉 CONSULTA EXITOSA - RETORNANDO RESULTADOS")
        logger.info("=" * 80)

        return results_panel, state, stepper, navigation, {"pointerEvents": "auto"}

    except Exception as e:
        logger.error("=" * 80)
        logger.error("💥 ERROR CRÍTICO EN EXECUTE_QUERY")
        logger.error("=" * 80)
        logger.error(f"Tipo: {type(e).__name__}")
        logger.error(f"Mensaje: {str(e)}")
        logger.error("Traceback completo:", exc_info=True)
        logger.error("=" * 80)

        state["query_processing"] = False

        error_panel = dbc.Alert(
            [
                html.I(className="bi bi-x-circle-fill me-2"),
                html.H5("Error Crítico", className="alert-heading"),
                html.P(f"Tipo: {type(e).__name__}"),
                html.P(f"Mensaje: {str(e)}"),
            ],
            color="danger",
            className="alert-savia",
        )

        return error_panel, state, no_update, no_update, {"pointerEvents": "auto"}


# ==================== CALLBACK DE DESCARGA ====================


@callback(
    Output("download-csv", "data"),
    Input("btn-download-csv", "n_clicks"),
    State("app-state", "data"),
    prevent_initial_call=True,
)
def download_csv(n_clicks, state):
    """Descarga archivo CSV."""
    if not n_clicks or n_clicks == 0:
        return no_update

    query_result = state.get("query_result", {})
    csv_filepath = query_result.get("csv_filepath")
    filename = query_result.get("filename", "RIPS_AC.csv")

    if not csv_filepath or not os.path.exists(csv_filepath):
        return no_update

    try:
        import base64

        with open(csv_filepath, "rb") as f:
            content = f.read()

        encoded = base64.b64encode(content).decode("utf-8")

        logger.info(f"✓ Descargando: {filename}")

        return {"content": encoded, "filename": filename, "base64": True}

    except Exception as e:
        logger.error(f"Error en descarga: {str(e)}")
        return no_update


# ==================== INICIAR APLICACIÓN ====================

if __name__ == "__main__":
    logger.info("Iniciando aplicación RIPS")
    app.run(debug=app_config.app_debug, port=app_config.app_port, host="0.0.0.0")
