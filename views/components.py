"""Componentes reutilizables para la UI con diseño Savia Salud."""

import dash_bootstrap_components as dbc
from dash import html, dcc
from datetime import date, timedelta
from typing import List

from utils.catalogs import CatalogNormalizer


class GlobalFiltersPanel:
    """Panel de filtros globales con diseño limpio sin accordions excesivos."""

    @staticmethod
    def create(normativa: str, rips_type: str = "AC"):
        """
        Crea panel completo de filtros globales todo visible.

        Args:
            normativa: Normativa seleccionada ('3374' o '2275')
            rips_type: Tipo de RIPS ('AC', 'AP', 'AH')
        """
        today = date.today()
        default_start = today - timedelta(days=30)

        return html.Div(
            [
                # Rango de fechas (OBLIGATORIO) - Con padding extra abajo
                html.Div(
                    [
                        html.Label(
                            [
                                html.I(
                                    className="bi bi-calendar-range me-2 text-savia-primary"
                                ),
                                "Rango de Fechas ",
                                dbc.Badge(
                                    "Obligatorio", color="danger", className="ms-2"
                                ),
                                dbc.Tooltip(
                                    "Período de tiempo para el cual se generará el reporte. Máximo 3 años.",
                                    target="tooltip-fecha-rango",
                                    placement="right",
                                ),
                            ],
                            className="fw-bold mb-3",
                            id="tooltip-fecha-rango",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label(
                                            [
                                                html.I(
                                                    className="bi bi-calendar-check me-1"
                                                ),
                                                "Fecha Inicio",
                                            ],
                                            className="small text-muted fw-bold",
                                        ),
                                        dcc.DatePickerSingle(
                                            id={
                                                "type": "date-picker-start",
                                                "rips": rips_type,
                                            },
                                            date=default_start,
                                            display_format="YYYY-MM-DD",
                                            placeholder="Seleccione fecha",
                                            className="w-100",
                                        ),
                                    ],
                                    md=6,
                                ),
                                dbc.Col(
                                    [
                                        html.Label(
                                            [
                                                html.I(
                                                    className="bi bi-calendar-x me-1"
                                                ),
                                                "Fecha Fin",
                                            ],
                                            className="small text-muted fw-bold",
                                        ),
                                        dcc.DatePickerSingle(
                                            id={
                                                "type": "date-picker-end",
                                                "rips": rips_type,
                                            },
                                            date=today,
                                            display_format="YYYY-MM-DD",
                                            placeholder="Seleccione fecha",
                                            className="w-100",
                                        ),
                                    ],
                                    md=6,
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                html.I(
                                    className="bi bi-info-circle me-1 text-savia-info"
                                ),
                                html.Small(
                                    "Rango máximo: 3 años", className="text-muted"
                                ),
                            ],
                            className="mt-2",
                        ),
                        html.Div(
                            id={"type": "date-validation-feedback", "rips": rips_type},
                            className="mt-2",
                        ),
                    ],
                    className="mb-4 pb-4",
                ),  # Padding extra para date picker
                html.Hr(className="my-4"),
                # Código prestador (opcional) - Sin accordion
                html.Div(
                    [
                        html.Label(
                            [
                                html.I(
                                    className="bi bi-building me-2 text-savia-primary"
                                ),
                                "Código Prestador ",
                                html.Small("(opcional)", className="text-muted"),
                            ],
                            className="fw-bold mb-2",
                        ),
                        html.Div(
                            [
                                html.I(
                                    className="bi bi-info-circle me-2 text-savia-info"
                                ),
                                html.Small(
                                    "Filtrar por prestadores específicos usando códigos REPS",
                                    className="text-muted",
                                ),
                            ],
                            className="mb-3",
                        ),
                        MultipleValuesInput.create(
                            input_id={
                                "type": "filter-codigo-prestador",
                                "rips": rips_type,
                            },
                            placeholder="Ejemplo: 800123456",
                            help_text="Códigos REPS de 10-12 dígitos",
                        ),
                    ],
                    className="mb-4",
                ),
                html.Hr(className="my-4"),
                # Documento usuario (opcional) - Sin accordion
                html.Div(
                    [
                        html.Label(
                            [
                                html.I(
                                    className="bi bi-person-vcard me-2 text-savia-primary"
                                ),
                                "Documento Usuario ",
                                html.Small("(opcional)", className="text-muted"),
                            ],
                            className="fw-bold mb-2",
                        ),
                        html.Div(
                            [
                                html.I(
                                    className="bi bi-info-circle me-2 text-savia-info"
                                ),
                                html.Small(
                                    "Filtrar por usuarios específicos usando números de documento",
                                    className="text-muted",
                                ),
                            ],
                            className="mb-3",
                        ),
                        MultipleValuesInput.create(
                            input_id={
                                "type": "filter-documento-usuario",
                                "rips": rips_type,
                            },
                            placeholder="Ejemplo: 1234567890",
                            help_text="Números de documento sin puntos ni guiones",
                        ),
                    ],
                    className="mb-4",
                ),
            ]
        )


class MultipleValuesInput:
    """Componente para entrada de múltiples valores simplificado."""

    @staticmethod
    def create(input_id: dict, placeholder: str = "", help_text: str = ""):
        """
        Crea componente de entrada múltiple: Lista (colapsado) o Archivo.

        Args:
            input_id: Dict con pattern-matching {'type': 'name', 'rips': 'AC'}
            placeholder: Texto de ejemplo
            help_text: Texto de ayuda
        """
        # Generar IDs derivados
        mode_id = {**input_id, "subtype": "mode"}
        lista_id = {**input_id, "subtype": "lista"}
        archivo_id = {**input_id, "subtype": "archivo"}
        values_id = {**input_id, "subtype": "values"}
        count_id = {**input_id, "subtype": "count"}
        lista_container_id = {**input_id, "subtype": "lista-container"}
        archivo_container_id = {**input_id, "subtype": "archivo-container"}
        archivo_info_id = {**input_id, "subtype": "archivo-info"}

        is_codigo_prestador = input_id.get("type") == "filter-codigo-prestador"

        return html.Div(
            [
                # Selector de modo simplificado
                dbc.RadioItems(
                    id=mode_id,
                    options=[
                        {"label": "Lista de valores", "value": "lista"},
                        {"label": "Cargar archivo", "value": "archivo"},
                    ],
                    value="lista",
                    inline=True,
                    className="mb-3",
                ),
                # Área de entrada lista (colapsado por defecto)
                html.Div(
                    [
                        dbc.Textarea(
                            id=lista_id,
                            placeholder="Ingrese valores separados por:\n• Coma (,)\n• Pipe (|)\n• Salto de línea",
                            rows=4,
                            className="mb-2",
                        ),
                        html.Small(
                            [html.I(className="bi bi-info-circle me-1"), help_text],
                            className="text-muted",
                        ),
                    ],
                    id=lista_container_id,
                ),
                # Área de carga de archivo
                html.Div(
                    [
                        dcc.Upload(
                            id=archivo_id,
                            children=dbc.Button(
                                [
                                    html.I(className="bi bi-cloud-arrow-up me-2"),
                                    "Seleccionar Archivo",
                                ],
                                color="secondary",
                                outline=True,
                                className="w-100",
                            ),
                            multiple=False,
                            className="mb-2",
                        ),
                        html.Div(id=archivo_info_id, className="mb-2"),
                        (
                            dbc.Alert(
                                [
                                    html.I(className="bi bi-exclamation-triangle me-2"),
                                    "Excel elimina ceros iniciales. Use CSV o formatee como TEXTO.",
                                ],
                                color="warning",
                                className="alert-savia mb-2",
                                style={"fontSize": "0.85rem"},
                            )
                            if is_codigo_prestador
                            else None
                        ),
                        html.Small(
                            [
                                html.I(className="bi bi-file-earmark me-1"),
                                (
                                    "Formatos: .csv, .txt (máx 2MB)"
                                    if is_codigo_prestador
                                    else "Formatos: .xlsx, .csv, .txt (máx 2MB)"
                                ),
                            ],
                            className="text-muted",
                        ),
                    ],
                    id=archivo_container_id,
                    style={"display": "none"},
                ),
                # Store y contador
                dcc.Store(id=values_id, data=[]),
                html.Div(id=count_id, className="mt-2"),
            ]
        )


class CategoricalInput:
    """Componente para variables categóricas con tooltips."""

    @staticmethod
    def create(
        input_id: dict, field_name: str, normativa: str, label: str, help_text: str = ""
    ):
        """
        Crea dropdown con opciones del catálogo y tooltip explicativo.

        Args:
            input_id: Dict con pattern-matching {'type': 'name', 'rips': 'AC'}
            field_name: Nombre del campo en catálogo
            normativa: Normativa seleccionada
            label: Etiqueta del componente
            help_text: Texto de ayuda opcional
        """
        options = CatalogNormalizer.get_catalog_options(field_name, normativa)

        dropdown_options = [
            {"label": f"{code} - {desc}", "value": code} for code, desc in options
        ]

        # ID único para tooltip
        tooltip_id = f"tooltip-{input_id['type']}-{input_id['rips']}"

        return html.Div(
            [
                html.Label(
                    [
                        label,
                        html.I(
                            className="bi bi-question-circle ms-2 text-savia-info",
                            id=tooltip_id,
                            style={"cursor": "pointer"},
                        ),
                        (
                            dbc.Tooltip(help_text, target=tooltip_id, placement="right")
                            if help_text
                            else None
                        ),
                    ],
                    className="fw-bold mb-2",
                ),
                dcc.Dropdown(
                    id=input_id,
                    options=dropdown_options,
                    multi=True,
                    placeholder=f"Seleccione uno o más valores ({len(dropdown_options)} disponibles)",
                    className="mb-2",
                ),
            ],
            className="mb-3",
        )


class RangeInput:
    """Componente para valores de rango con validación visual."""

    @staticmethod
    def create(
        input_id: dict,
        label: str,
        min_placeholder: str = "Mínimo",
        max_placeholder: str = "Máximo",
        help_text: str = "",
    ):
        """
        Crea input de rango numérico con validación visual.

        Args:
            input_id: Dict con pattern-matching {'type': 'name', 'rips': 'AC'}
            label: Etiqueta del componente
            min_placeholder: Placeholder para valor mínimo
            max_placeholder: Placeholder para valor máximo
            help_text: Texto de ayuda opcional
        """
        # Generar IDs para min y max
        min_id = {**input_id, "subtype": "min"}
        max_id = {**input_id, "subtype": "max"}

        # ID único para tooltip
        tooltip_id = f"tooltip-{input_id['type']}-{input_id['rips']}"

        return html.Div(
            [
                html.Label(
                    [
                        html.I(
                            className="bi bi-currency-dollar me-2 text-savia-primary"
                        ),
                        label,
                        (
                            html.I(
                                className="bi bi-question-circle ms-2 text-savia-info",
                                id=tooltip_id,
                                style={"cursor": "pointer"},
                            )
                            if help_text
                            else None
                        ),
                        (
                            dbc.Tooltip(help_text, target=tooltip_id, placement="right")
                            if help_text
                            else None
                        ),
                    ],
                    className="fw-bold mb-2",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.InputGroup(
                                    [
                                        dbc.InputGroupText(
                                            [
                                                html.I(
                                                    className="bi bi-arrow-down-circle"
                                                )
                                            ]
                                        ),
                                        dbc.Input(
                                            id=min_id,
                                            type="number",
                                            placeholder=min_placeholder,
                                            min=0,
                                            step=1,
                                        ),
                                    ]
                                )
                            ],
                            md=6,
                        ),
                        dbc.Col(
                            [
                                dbc.InputGroup(
                                    [
                                        dbc.InputGroupText(
                                            [html.I(className="bi bi-arrow-up-circle")]
                                        ),
                                        dbc.Input(
                                            id=max_id,
                                            type="number",
                                            placeholder=max_placeholder,
                                            min=0,
                                            step=1,
                                        ),
                                    ]
                                )
                            ],
                            md=6,
                        ),
                    ]
                ),
            ],
            className="mb-3",
        )


class ColumnSelector:
    """Selector de columnas con diseño mejorado."""

    @staticmethod
    def create(
        rips_type: str, available_columns: List[str], selected_columns: List[str] = None
    ):
        """
        Crea selector de columnas con select all y scroll mejorado.

        Args:
            rips_type: Tipo de RIPS ('AC', 'AP', 'AH')
            available_columns: Lista de columnas disponibles
            selected_columns: Lista de columnas pre-seleccionadas
        """
        if selected_columns is None:
            selected_columns = []

        return html.Div(
            [
                # Header con badge de conteo
                html.Div(
                    [
                        dbc.Button(
                            [
                                html.I(className="bi bi-check-all me-2"),
                                "Seleccionar todas",
                            ],
                            id={"type": "btn-select-all-columns", "rips": rips_type},
                            color="link",
                            size="sm",
                            className="p-0 text-savia-primary fw-bold",
                        ),
                        dbc.Badge(
                            f"{len(available_columns)} disponibles",
                            color="secondary",
                            className="ms-2",
                        ),
                    ],
                    className="d-flex align-items-center justify-content-between mb-2",
                ),
                # Checklist con scroll mejorado
                dbc.Checklist(
                    id={"type": "checklist-columns", "rips": rips_type},
                    options=[
                        {
                            "label": html.Div(
                                [
                                    html.I(
                                        className="bi bi-check-circle me-2 text-success",
                                        style={"fontSize": "0.9em"},
                                    ),
                                    col,
                                ],
                                className="d-flex align-items-center",
                            ),
                            "value": col,
                        }
                        for col in available_columns
                    ],
                    value=selected_columns,
                    className="column-checklist",
                ),
                # Footer con conteo de seleccionadas
                html.Small(
                    [
                        html.I(className="bi bi-info-circle me-1"),
                        html.Span(
                            f"{len(selected_columns)} de {len(available_columns)} seleccionadas",
                            id={"type": "columns-selected-count", "rips": rips_type},
                        ),
                    ],
                    className="text-muted d-block mt-2",
                ),
            ]
        )


class QuerySummary:
    """Panel de resumen con diseño moderno y ListGroup."""

    @staticmethod
    def create(summary_data: dict):
        """
        Crea panel de resumen con ListGroup y badges.

        Args:
            summary_data: Diccionario con datos del resumen
        """
        is_valid = summary_data.get("is_valid", False)

        return html.Div(
            [
                # Información principal en ListGroup
                dbc.ListGroup(
                    [
                        dbc.ListGroupItem(
                            [
                                html.Div(
                                    [
                                        html.I(
                                            className="bi bi-file-text me-2 text-savia-primary"
                                        ),
                                        html.Strong("Normativa:"),
                                    ],
                                    className="d-inline-block",
                                    style={"width": "120px"},
                                ),
                                html.Span(
                                    summary_data.get("normativa", "No seleccionada")
                                ),
                            ],
                            className="d-flex justify-content-between align-items-center",
                        ),
                        dbc.ListGroupItem(
                            [
                                html.Div(
                                    [
                                        html.I(
                                            className="bi bi-card-list me-2 text-savia-primary"
                                        ),
                                        html.Strong("Tipo RIPS:"),
                                    ],
                                    className="d-inline-block",
                                    style={"width": "120px"},
                                ),
                                dbc.Badge(
                                    summary_data.get("tipo", "No seleccionado"),
                                    color="primary",
                                    className="badge-savia",
                                ),
                            ],
                            className="d-flex justify-content-between align-items-center",
                        ),
                        dbc.ListGroupItem(
                            [
                                html.Div(
                                    [
                                        html.I(
                                            className="bi bi-calendar-range me-2 text-savia-primary"
                                        ),
                                        html.Strong("Período:"),
                                    ],
                                    className="d-inline-block",
                                    style={"width": "120px"},
                                ),
                                html.Span(
                                    f"{summary_data.get('fecha_inicio', '')} → {summary_data.get('fecha_fin', '')}",
                                    className="small",
                                ),
                            ],
                            className="d-flex justify-content-between align-items-center",
                        ),
                    ],
                    flush=True,
                    className="mb-3",
                ),
                # Estadísticas de configuración
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.I(
                                            className="bi bi-globe text-savia-primary",
                                            style={"fontSize": "1.5rem"},
                                        ),
                                        html.Div(
                                            [
                                                html.H4(
                                                    summary_data.get(
                                                        "num_filtros_globales", 0
                                                    ),
                                                    className="mb-0",
                                                ),
                                                html.Small(
                                                    "Filtros Globales",
                                                    className="text-muted",
                                                ),
                                            ]
                                        ),
                                    ],
                                    className="text-center",
                                )
                            ],
                            width=4,
                        ),
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.I(
                                            className="bi bi-sliders text-savia-primary",
                                            style={"fontSize": "1.5rem"},
                                        ),
                                        html.Div(
                                            [
                                                html.H4(
                                                    summary_data.get(
                                                        "num_filtros_especificos", 0
                                                    ),
                                                    className="mb-0",
                                                ),
                                                html.Small(
                                                    "Filtros Específicos",
                                                    className="text-muted",
                                                ),
                                            ]
                                        ),
                                    ],
                                    className="text-center",
                                )
                            ],
                            width=4,
                        ),
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.I(
                                            className="bi bi-table text-savia-primary",
                                            style={"fontSize": "1.5rem"},
                                        ),
                                        html.Div(
                                            [
                                                html.H4(
                                                    summary_data.get("num_columnas", 0),
                                                    className="mb-0",
                                                ),
                                                html.Small(
                                                    "Columnas", className="text-muted"
                                                ),
                                            ]
                                        ),
                                    ],
                                    className="text-center",
                                )
                            ],
                            width=4,
                        ),
                    ],
                    className="mb-3",
                ),
                # Alert de estado
                dbc.Alert(
                    [
                        html.I(
                            className=f"bi bi-{'check-circle-fill' if is_valid else 'exclamation-triangle-fill'} me-2"
                        ),
                        html.Strong(
                            "Listo para generar"
                            if is_valid
                            else "Complete la configuración"
                        ),
                    ],
                    color="success" if is_valid else "warning",
                    className="alert-savia mb-0",
                ),
            ]
        )


class ProgressIndicator:
    """Indicador de progreso para consultas largas."""

    @staticmethod
    def create(show: bool = False, percentage: int = 0, message: str = ""):
        """
        Crea indicador de progreso animado.

        Args:
            show: Si se muestra o no
            percentage: Porcentaje de progreso (0-100)
            message: Mensaje descriptivo
        """
        if not show:
            return html.Div(style={"display": "none"})

        return dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                dbc.Spinner(
                                    color="primary",
                                    spinner_className="spinner-savia",
                                    size="lg",
                                ),
                                html.H5(
                                    message or "Procesando consulta...",
                                    className="mt-3 mb-3",
                                ),
                            ],
                            className="text-center",
                        ),
                        dbc.Progress(
                            value=percentage,
                            striped=True,
                            animated=True,
                            className="mb-2",
                            style={"height": "20px"},
                            color="primary",
                        ),
                        html.Div(
                            [
                                html.I(className="bi bi-info-circle me-2"),
                                html.Small(
                                    f"Progreso: {percentage}%", className="text-muted"
                                ),
                            ],
                            className="text-center",
                        ),
                    ]
                )
            ],
            className="card-savia",
        )
