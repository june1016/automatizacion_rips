"""Vista específica para tipo RIPS AC con diseño Savia Salud."""

import dash_bootstrap_components as dbc
from dash import html

from views.components import (
    MultipleValuesInput,
    CategoricalInput,
    RangeInput,
    ColumnSelector,
)
from models.ac_model import AC_EXPORT_COLUMNS


class ACFiltersPanel:
    """Panel de filtros específicos para AC."""

    @staticmethod
    def create(normativa: str, rips_type: str = "AC"):
        """
        Crea panel de filtros específicos de AC.

        Args:
            normativa: Normativa seleccionada ('3374' o '2275')
            rips_type: Tipo de RIPS ('AC')
        """
        return html.Div(
            [
                dbc.Alert(
                    [
                        html.I(className="bi bi-info-circle-fill me-2"),
                        "Configure filtros específicos para consultas (AC). Todos los campos son opcionales.",
                    ],
                    color="info",
                    className="alert-savia mb-4",
                ),
                # Clasificación de Consulta
                html.Div(
                    [
                        html.H6(
                            [
                                html.I(
                                    className="bi bi-clipboard2-pulse me-2 text-savia-primary"
                                ),
                                "Clasificación de Consulta",
                            ],
                            className="fw-bold text-savia-secondary mb-3",
                        ),
                        CategoricalInput.create(
                            input_id={
                                "type": "filter-finalidad-consulta",
                                "rips": rips_type,
                            },
                            field_name="finalidad_consulta",
                            normativa=normativa,
                            label="Finalidad de Consulta",
                            help_text="Motivo por el cual se realiza la atención",
                        ),
                        CategoricalInput.create(
                            input_id={
                                "type": "filter-causa-externa",
                                "rips": rips_type,
                            },
                            field_name="causa_externa",
                            normativa=normativa,
                            label="Causa Externa",
                            help_text="Causa que originó la atención médica",
                        ),
                    ],
                    className="mb-4",
                ),
                html.Hr(className="my-4"),
                # Diagnósticos CIE-10
                html.Div(
                    [
                        html.H6(
                            [
                                html.I(
                                    className="bi bi-heart-pulse me-2 text-savia-primary"
                                ),
                                "Diagnósticos CIE-10",
                            ],
                            className="fw-bold text-savia-secondary mb-3",
                        ),
                        html.Small(
                            "Configure diagnósticos según códigos CIE-10. Principal y hasta 3 relacionados.",
                            className="text-muted d-block mb-3",
                        ),
                        # Diagnóstico principal con botón para aplicar a todos
                        html.Div(
                            [
                                html.Label(
                                    "Diagnóstico Principal (CIE-10)",
                                    className="fw-bold mb-2",
                                ),
                                MultipleValuesInput.create(
                                    input_id={
                                        "type": "filter-diagnostico-principal",
                                        "rips": rips_type,
                                    },
                                    placeholder="Ejemplo: A00, B01, C15",
                                    help_text="Códigos CIE-10 del diagnóstico principal",
                                ),
                                # Botón explícito para aplicar diagnósticos a todos los campos
                                dbc.Button(
                                    [
                                        html.I(className="bi bi-copy me-2"),
                                        "Aplicar estos diagnósticos a todos los relacionados",
                                    ],
                                    id="btn-apply-diag-all",
                                    color="link",
                                    size="sm",
                                    className="mt-2 p-0 text-savia-primary",
                                    style={"fontSize": "0.9rem"},
                                ),
                            ],
                            className="mb-3",
                        ),
                        # Botón toggle diagnósticos relacionados
                        dbc.Button(
                            [
                                html.I(
                                    className="bi bi-plus-circle me-2",
                                    id="icon-diag-relacionados",
                                ),
                                "Mostrar Diagnósticos Relacionados (Opcional)",
                            ],
                            id="btn-toggle-diag-relacionados",
                            color="link",
                            className="p-0 mb-2 text-savia-primary",
                        ),
                        # Collapse con diagnósticos relacionados
                        dbc.Collapse(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.Label(
                                                    "Diagnóstico Relacionado 1",
                                                    className="fw-bold mb-2",
                                                ),
                                                MultipleValuesInput.create(
                                                    input_id={
                                                        "type": "filter-diagnostico-relacionado-1",
                                                        "rips": rips_type,
                                                    },
                                                    placeholder="Ejemplo: A00, B01",
                                                    help_text="Primer diagnóstico relacionado",
                                                ),
                                            ],
                                            className="mb-3",
                                        ),
                                        html.Div(
                                            [
                                                html.Label(
                                                    "Diagnóstico Relacionado 2",
                                                    className="fw-bold mb-2",
                                                ),
                                                MultipleValuesInput.create(
                                                    input_id={
                                                        "type": "filter-diagnostico-relacionado-2",
                                                        "rips": rips_type,
                                                    },
                                                    placeholder="Ejemplo: A00, B01",
                                                    help_text="Segundo diagnóstico relacionado",
                                                ),
                                            ],
                                            className="mb-3",
                                        ),
                                        html.Div(
                                            [
                                                html.Label(
                                                    "Diagnóstico Relacionado 3",
                                                    className="fw-bold mb-2",
                                                ),
                                                MultipleValuesInput.create(
                                                    input_id={
                                                        "type": "filter-diagnostico-relacionado-3",
                                                        "rips": rips_type,
                                                    },
                                                    placeholder="Ejemplo: A00, B01",
                                                    help_text="Tercer diagnóstico relacionado",
                                                ),
                                            ],
                                            className="mb-3",
                                        ),
                                    ],
                                    className="p-3 bg-light rounded",
                                )
                            ],
                            id="collapse-diag-relacionados",
                            is_open=False,
                        ),
                        html.Div(className="mb-3"),
                        CategoricalInput.create(
                            input_id={
                                "type": "filter-tipo-diagnostico-principal",
                                "rips": rips_type,
                            },
                            field_name="tipo_diagnostico_principal",
                            normativa=normativa,
                            label="Tipo de Diagnóstico Principal",
                            help_text="Clasificación del diagnóstico (Confirmado, Presuntivo, etc.)",
                        ),
                    ],
                    className="mb-4",
                ),
                html.Hr(className="my-4"),
                # Valor de Consulta
                html.Div(
                    [
                        html.H6(
                            [
                                html.I(
                                    className="bi bi-currency-dollar me-2 text-savia-primary"
                                ),
                                "Valor de Consulta",
                            ],
                            className="fw-bold text-savia-secondary mb-3",
                        ),
                        html.Div(
                            [
                                html.I(
                                    className="bi bi-info-circle me-2 text-savia-info"
                                ),
                                html.Small(
                                    "Filtre consultas por rango de valor en pesos colombianos (COP).",
                                    className="text-muted",
                                ),
                            ],
                            className="mb-3",
                        ),
                        RangeInput.create(
                            input_id={
                                "type": "filter-valor-consulta",
                                "rips": rips_type,
                            },
                            label="Rango de Valor",
                            min_placeholder="Valor mínimo (COP)",
                            max_placeholder="Valor máximo (COP)",
                            help_text="Rango de valores en pesos colombianos. Ambos campos son opcionales.",
                        ),
                    ]
                ),
            ]
        )


class ACColumnsPanel:
    """Panel de selección de columnas para AC."""

    @staticmethod
    def create(normativa: str, rips_type: str = "AC", selected_columns: list = None):
        """
        Crea panel de selección de columnas.

        Args:
            normativa: Normativa seleccionada ('3374' o '2275')
            rips_type: Tipo de RIPS ('AC')
            selected_columns: Lista de columnas pre-seleccionadas
        """
        available_columns = AC_EXPORT_COLUMNS.get(normativa, [])

        return html.Div(
            [
                dbc.Alert(
                    [
                        html.I(className="bi bi-table me-2"),
                        "Seleccione las columnas que desea incluir en el reporte CSV. ",
                        dbc.Badge(
                            "Nivel 1", color="primary", className="badge-savia ms-2"
                        ),
                        html.Small(
                            " Variables normativas", className="text-muted ms-1"
                        ),
                    ],
                    color="light",
                    className="mb-3",
                ),
                ColumnSelector.create(
                    rips_type=rips_type,
                    available_columns=available_columns,
                    selected_columns=selected_columns or [],
                ),
            ]
        )


class ACResultsPanel:
    """Panel de resultados y descarga para AC."""

    @staticmethod
    def create(query_result: dict, rips_type: str = "AC"):
        """
        Crea panel de resultados después de ejecutar consulta.

        Args:
            query_result: Diccionario con resultados de la consulta
            rips_type: Tipo de RIPS ('AC')
        """
        if not query_result.get("success", False):
            return dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="bi bi-x-circle-fill text-danger",
                                        style={"fontSize": "4rem"},
                                    ),
                                    html.H3(
                                        "Error en la Consulta",
                                        className="text-danger mt-3 mb-3",
                                    ),
                                ],
                                className="text-center",
                            ),
                            dbc.Alert(
                                [
                                    html.Strong("Mensaje: "),
                                    html.Span(
                                        query_result.get("message", "Error desconocido")
                                    ),
                                ],
                                color="danger",
                                className="alert-savia",
                            ),
                            (
                                dbc.Alert(
                                    [
                                        html.Strong("Detalles técnicos: "),
                                        html.Br(),
                                        html.Code(
                                            query_result.get(
                                                "error_details",
                                                "Sin detalles disponibles",
                                            ),
                                            className="text-muted small",
                                        ),
                                    ],
                                    color="light",
                                    className="alert-savia",
                                )
                                if query_result.get("error_details")
                                else None
                            ),
                        ]
                    )
                ],
                className="card-savia",
            )

        # Consulta exitosa
        return dbc.Card(
            [
                dbc.CardBody(
                    [
                        # Header de éxito
                        html.Div(
                            [
                                html.I(
                                    className="bi bi-check-circle-fill text-success",
                                    style={"fontSize": "4rem"},
                                ),
                                html.H3(
                                    "¡Reporte Generado Exitosamente!",
                                    className="text-success mt-3 mb-4",
                                ),
                            ],
                            className="text-center",
                        ),
                        # Estadísticas
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardBody(
                                                    [
                                                        html.I(
                                                            className="bi bi-file-text text-savia-primary",
                                                            style={
                                                                "fontSize": "2.5rem"
                                                            },
                                                        ),
                                                        html.H2(
                                                            f"{query_result.get('record_count', 0):,}",
                                                            className="mt-2 mb-0 text-savia-primary",
                                                        ),
                                                        html.Small(
                                                            "Registros",
                                                            className="text-muted text-uppercase",
                                                        ),
                                                    ],
                                                    className="text-center py-3",
                                                )
                                            ],
                                            className="card-savia bg-savia-light",
                                        )
                                    ],
                                    md=4,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardBody(
                                                    [
                                                        html.I(
                                                            className="bi bi-stopwatch text-savia-primary",
                                                            style={
                                                                "fontSize": "2.5rem"
                                                            },
                                                        ),
                                                        html.H2(
                                                            f"{query_result.get('execution_time', 0):.2f}s",
                                                            className="mt-2 mb-0 text-savia-primary",
                                                        ),
                                                        html.Small(
                                                            "Tiempo de Ejecución",
                                                            className="text-muted text-uppercase",
                                                        ),
                                                    ],
                                                    className="text-center py-3",
                                                )
                                            ],
                                            className="card-savia bg-savia-light",
                                        )
                                    ],
                                    md=4,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardBody(
                                                    [
                                                        html.I(
                                                            className="bi bi-hdd-network text-savia-primary",
                                                            style={
                                                                "fontSize": "2.5rem"
                                                            },
                                                        ),
                                                        html.H2(
                                                            ", ".join(
                                                                query_result.get(
                                                                    "connections_used",
                                                                    [],
                                                                )
                                                            ),
                                                            className="mt-2 mb-0 text-savia-primary",
                                                            style={
                                                                "fontSize": "1.5rem"
                                                            },
                                                        ),
                                                        html.Small(
                                                            "Conexiones BD",
                                                            className="text-muted text-uppercase",
                                                        ),
                                                    ],
                                                    className="text-center py-3",
                                                )
                                            ],
                                            className="card-savia bg-savia-light",
                                        )
                                    ],
                                    md=4,
                                ),
                            ],
                            className="mb-4",
                        ),
                        html.Hr(),
                        # Descarga
                        html.Div(
                            [
                                html.H5(
                                    [
                                        html.I(className="bi bi-download me-2"),
                                        "Descargar Archivo",
                                    ],
                                    className="text-savia-secondary mb-3",
                                ),
                                dbc.Button(
                                    [
                                        html.I(
                                            className="bi bi-file-earmark-arrow-down me-2",
                                            style={"fontSize": "1.5rem"},
                                        ),
                                        html.Span(
                                            "Descargar CSV",
                                            style={"fontSize": "1.2rem"},
                                        ),
                                    ],
                                    id="btn-download-csv",
                                    n_clicks=0,
                                    color="success",
                                    size="lg",
                                    className="w-100 py-3 mb-3",
                                ),
                                dbc.Card(
                                    [
                                        dbc.CardBody(
                                            [
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            [
                                                                html.Div(
                                                                    [
                                                                        html.I(
                                                                            className="bi bi-file-earmark-text me-2 text-muted"
                                                                        ),
                                                                        html.Strong(
                                                                            "Archivo:"
                                                                        ),
                                                                    ],
                                                                    className="small text-muted",
                                                                ),
                                                                html.Code(
                                                                    query_result.get(
                                                                        "filename",
                                                                        "RIPS_AC.csv",
                                                                    ),
                                                                    className="text-savia-primary",
                                                                ),
                                                            ],
                                                            md=6,
                                                        ),
                                                        dbc.Col(
                                                            [
                                                                html.Div(
                                                                    [
                                                                        html.I(
                                                                            className="bi bi-filetype-csv me-2 text-muted"
                                                                        ),
                                                                        html.Strong(
                                                                            "Formato:"
                                                                        ),
                                                                    ],
                                                                    className="small text-muted",
                                                                ),
                                                                html.Span(
                                                                    "CSV (UTF-8 con BOM)",
                                                                    className="small",
                                                                ),
                                                            ],
                                                            md=6,
                                                        ),
                                                    ]
                                                )
                                            ]
                                        )
                                    ],
                                    className="card-savia bg-savia-light",
                                ),
                            ]
                        ),
                        html.Hr(className="my-4"),
                        # Información adicional
                        dbc.Alert(
                            [
                                html.I(className="bi bi-info-circle-fill me-2"),
                                html.Strong("Información del archivo:"),
                                html.Ul(
                                    [
                                        html.Li("Separador: punto y coma (;)"),
                                        html.Li("Codificación: UTF-8 con BOM"),
                                        html.Li(
                                            "Compatible con Excel y herramientas de análisis"
                                        ),
                                        html.Li(
                                            "Valores normalizados según catálogos oficiales"
                                        ),
                                    ],
                                    className="mb-0 mt-2",
                                ),
                            ],
                            color="info",
                            className="alert-savia mb-0",
                        ),
                    ]
                )
            ],
            className="card-savia",
        )


class ACActionsPanel:
    """Panel de acciones para AC."""

    @staticmethod
    def create(rips_type: str = "AC"):
        """
        Crea panel con botón de generar reporte.

        Args:
            rips_type: Tipo de RIPS ('AC')
        """
        return html.Div(
            [
                html.H5(
                    [
                        html.I(
                            className="bi bi-rocket-takeoff me-2 text-savia-primary"
                        ),
                        "Generar Reporte",
                    ],
                    className="mb-3 text-savia-secondary",
                ),
                # Límites consolidados
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H6("Límites de Carga", className="mb-3"),
                                html.Ul(
                                    [
                                        html.Li(
                                            [
                                                html.Strong("Lista: "),
                                                "Hasta 1,000 valores",
                                            ]
                                        ),
                                        html.Li(
                                            [
                                                html.Strong("Archivo: "),
                                                "Hasta 1,000 valores",
                                            ]
                                        ),
                                        html.Li(
                                            [
                                                html.Strong("Consulta: "),
                                                "Hasta 750,000 registros",
                                            ]
                                        ),
                                        html.Li(
                                            [html.Strong("Rango: "), "Máximo 3 años"]
                                        ),
                                    ],
                                    className="mb-0 small",
                                ),
                            ]
                        )
                    ],
                    className="card-savia bg-savia-light mb-3",
                ),
                dbc.Alert(
                    [
                        html.I(className="bi bi-lightbulb me-2"),
                        "Configure al menos un filtro específico para optimizar tiempos de consulta.",
                    ],
                    color="info",
                    className="alert-savia mb-3",
                    style={"fontSize": "0.85rem"},
                ),
                # Botón principal
                dbc.Button(
                    [
                        html.I(
                            className="bi bi-play-circle-fill me-2",
                            style={"fontSize": "1.2rem"},
                        ),
                        "Generar Reporte",
                    ],
                    id={"type": "btn-generar-reporte", "rips": rips_type},
                    color="primary",
                    size="lg",
                    className="w-100 py-3",
                ),
            ]
        )
