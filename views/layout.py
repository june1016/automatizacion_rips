"""Layout principal de la aplicación - Estructura multi-paso con diseño Savia Salud."""

import dash_bootstrap_components as dbc
from dash import html, dcc


class AppLayout:
    """Layout base de la aplicación con diseño profesional Savia Salud."""

    STEPS = [
        {"id": 0, "name": "Inicio", "icon": "bi-house-door"},
        {"id": 1, "name": "Normativa", "icon": "bi-file-text"},
        {"id": 2, "name": "Tipo RIPS", "icon": "bi-card-list"},
        {"id": 3, "name": "Configuración", "icon": "bi-sliders"},
        {"id": 5, "name": "Resultados", "icon": "bi-download"},
    ]

    @staticmethod
    def create_layout():
        """Crea layout completo de la aplicación."""
        return html.Div(
            [
                # ========== LOADING OVERLAY GLOBAL ==========
                html.Div(
                    [
                        html.Div(
                            [
                                dbc.Spinner(
                                    color="primary",
                                    spinner_style={
                                        "width": "4rem",
                                        "height": "4rem",
                                        "borderWidth": "0.4rem",
                                    },
                                ),
                                html.H4(
                                    "Cargando Sistema RIPS...",
                                    className="mt-4 text-white fw-bold",
                                ),
                                html.P(
                                    "Inicializando componentes",
                                    className="text-white-50 loading-message",
                                ),
                            ],
                            className="loading-content",
                        )
                    ],
                    id="global-loading-overlay",
                    className="global-loading-overlay",
                ),
                # Navbar profesional
                AppLayout._create_navbar(),
                # Contenedor principal
                dbc.Container(
                    [
                        # Stepper circular SIN card
                        html.Div(
                            id="progress-container",
                            children=AppLayout._create_stepper(0),
                            className="mt-4 mb-4",
                        ),
                        # Store de estado global
                        dcc.Store(
                            id="app-state",
                            data={
                                "current_step": 0,
                                "normativa": None,
                                "tipo_rips": None,
                                "global_filters": {},
                                "specific_filters": {},
                                "selected_columns": {},
                                "query_processing": False,
                            },
                        ),
                        # Store para trigger de loading (comunicación Python → JavaScript)
                        dcc.Store(
                            id="loading-trigger",
                            data={"show": False, "step": 0, "timestamp": 0},
                        ),
                        # Spinner overlay para queries largas
                        html.Div(
                            [
                                dbc.Spinner(
                                    color="primary",
                                    spinner_style={"width": "3rem", "height": "3rem"},
                                ),
                                html.P(
                                    "Consultando bases de datos...",
                                    className="mt-3 text-white fw-bold",
                                ),
                            ],
                            id="loading-overlay",
                            className="loading-overlay",
                            style={"display": "none"},
                        ),
                        # Área de contenido dinámico
                        html.Div(
                            id="main-content",
                            children=StepContent.step_0_inicio(),
                            className="fade-in",
                        ),
                        # Footer con navegación
                        html.Div(
                            id="navigation-footer",
                            children=AppLayout._create_navigation_footer(
                                current_step=0,
                                can_go_back=False,
                                can_go_forward=True,
                                forward_label="Siguiente",
                            ),
                            className="navigation-footer",
                        ),
                        # Contenedores dinámicos
                        html.Div(id="results-container", style={"display": "none"}),
                        html.Div(
                            id="panel-filtros-globales", style={"display": "none"}
                        ),
                        html.Div(
                            id="panel-filtros-especificos", style={"display": "none"}
                        ),
                        html.Div(id="panel-columnas", style={"display": "none"}),
                        html.Div(id="panel-resumen", style={"display": "none"}),
                        html.Div(id="panel-acciones", style={"display": "none"}),
                        # Placeholder botón descarga
                        html.Div(
                            [
                                dbc.Button(
                                    "Descargar CSV",
                                    id="btn-download-csv",
                                    n_clicks=0,
                                    style={"display": "none"},
                                )
                            ]
                        ),
                        dcc.Download(id="download-csv"),
                    ],
                    fluid=True,
                    className="py-4",
                ),
                # Modales
                AppLayout._create_modals(),
            ]
        )

    @staticmethod
    def _create_navbar():
        """Crea navbar profesional con marca Savia Salud."""
        return dbc.Navbar(
            dbc.Container(
                [
                    dbc.NavbarBrand(
                        [
                            html.I(className="bi bi-heart-pulse-fill me-2"),
                            "SAVIA Salud",
                            html.Span(" | RIPS", className="fw-normal"),
                        ]
                    ),
                    dbc.NavbarToggler(id="navbar-toggler"),
                    dbc.Collapse(
                        dbc.Nav(
                            [
                                dbc.NavItem(
                                    dbc.NavLink(
                                        [
                                            html.I(className="bi bi-house me-1"),
                                            "Inicio",
                                        ],
                                        href="#",
                                    )
                                ),
                                dbc.NavItem(
                                    dbc.NavLink(
                                        [
                                            html.I(className="bi bi-info-circle me-1"),
                                            "Ayuda",
                                        ],
                                        href="#",
                                    )
                                ),
                                dbc.NavItem(
                                    dbc.NavLink(
                                        [
                                            html.I(
                                                className="bi bi-person-circle me-2"
                                            ),
                                            "Admin",
                                        ],
                                        href="#",
                                    )
                                ),
                            ],
                            className="ms-auto",
                            navbar=True,
                        ),
                        id="navbar-collapse",
                        navbar=True,
                    ),
                ],
                fluid=True,
            ),
            color="primary",
            dark=True,
            className="navbar-savia mb-0",
            sticky="top",
        )

    @staticmethod
    def _create_stepper(current_step: int):
        """Crea stepper circular SIN card (sin fondo blanco)."""
        steps_components = []

        for i, step in enumerate(AppLayout.STEPS):
            step_id = step["id"]
            is_active = step_id == current_step
            is_completed = step_id < current_step

            # Determinar estado visual
            if is_completed:
                circle_class = "step-circle-completed"
                icon = html.I(className="bi bi-check2", style={"fontSize": "1.5rem"})
            elif is_active:
                circle_class = "step-circle-active"
                icon = html.I(
                    className=f"bi {step['icon']}", style={"fontSize": "1.2rem"}
                )
            else:
                circle_class = "step-circle-pending"
                icon = html.I(
                    className=f"bi {step['icon']}", style={"fontSize": "1.2rem"}
                )

            # Círculo del paso
            step_component = html.Div(
                [
                    html.Div(icon, className=f"step-circle {circle_class}"),
                    html.Div(step["name"], className="step-label"),
                ],
                className="step-item",
            )

            steps_components.append(step_component)

            # Conector entre pasos
            if i < len(AppLayout.STEPS) - 1:
                connector_class = (
                    "step-connector-completed"
                    if is_completed
                    else "step-connector-pending"
                )
                steps_components.append(
                    html.Div(className=f"step-connector {connector_class}")
                )

        # Retornar DIV directo sin Card (sin fondo blanco)
        return html.Div(
            html.Div(steps_components, className="stepper-container"), className="py-3"
        )

    @staticmethod
    def _create_modals():
        """Crea modales funcionales con diseño Savia."""
        return html.Div(
            [
                # Modal: Aplicar diagnósticos CIE-10 a todos los campos
                dbc.Modal(
                    [
                        dbc.ModalHeader(
                            dbc.ModalTitle(
                                [
                                    html.I(
                                        className="bi bi-question-circle-fill me-2 text-primary"
                                    ),
                                    "Aplicar Diagnósticos CIE-10",
                                ]
                            ),
                            className="modal-header-savia",
                        ),
                        dbc.ModalBody(
                            [
                                html.P(
                                    [
                                        "Ha cargado ",
                                        html.Strong(id="modal-diag-count"),
                                        " códigos diagnósticos CIE-10 en el campo principal.",
                                    ]
                                ),
                                html.P(
                                    "¿Desea copiar estos mismos valores a todos los campos de diagnósticos relacionados?"
                                ),
                                dbc.ListGroup(
                                    [
                                        dbc.ListGroupItem(
                                            [
                                                html.I(
                                                    className="bi bi-check-circle me-2 text-success"
                                                ),
                                                "Diagnóstico principal (ya cargado)",
                                            ]
                                        ),
                                        dbc.ListGroupItem(
                                            [
                                                html.I(
                                                    className="bi bi-arrow-right me-2 text-primary"
                                                ),
                                                "Diagnóstico relacionado 1",
                                            ]
                                        ),
                                        dbc.ListGroupItem(
                                            [
                                                html.I(
                                                    className="bi bi-arrow-right me-2 text-primary"
                                                ),
                                                "Diagnóstico relacionado 2",
                                            ]
                                        ),
                                        dbc.ListGroupItem(
                                            [
                                                html.I(
                                                    className="bi bi-arrow-right me-2 text-primary"
                                                ),
                                                "Diagnóstico relacionado 3",
                                            ]
                                        ),
                                    ],
                                    flush=True,
                                    className="mt-3",
                                ),
                            ]
                        ),
                        dbc.ModalFooter(
                            [
                                dbc.Button(
                                    "No, solo principal",
                                    id="modal-diag-only-principal",
                                    color="secondary",
                                    className="me-2",
                                ),
                                dbc.Button(
                                    "Sí, copiar a todos",
                                    id="modal-diag-all",
                                    color="primary",
                                ),
                            ]
                        ),
                    ],
                    id="modal-diagnosticos",
                    is_open=False,
                    centered=True,
                ),
                # Modal: Error crítico
                dbc.Modal(
                    [
                        dbc.ModalHeader(
                            dbc.ModalTitle(
                                [html.I(className="bi bi-x-circle-fill me-2"), "Error"],
                                className="text-danger",
                            ),
                            className="modal-header-savia",
                        ),
                        dbc.ModalBody(id="modal-error-body"),
                        dbc.ModalFooter(
                            [
                                dbc.Button(
                                    "Cerrar", id="modal-error-close", color="secondary"
                                )
                            ]
                        ),
                    ],
                    id="modal-error",
                    is_open=False,
                    centered=True,
                ),
            ]
        )

    @staticmethod
    def _create_navigation_footer(
        current_step: int,
        can_go_back: bool = True,
        can_go_forward: bool = False,
        forward_label: str = "Siguiente",
    ):
        """Crea footer de navegación con botones siempre renderizados."""
        return dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Button(
                            [html.I(className="bi bi-arrow-left me-2"), "Atrás"],
                            id="btn-back",
                            color="secondary",
                            outline=True,
                            disabled=not can_go_back or current_step == 0,
                            className="btn-lg",
                        )
                    ],
                    width="auto",
                ),
                dbc.Col(
                    [
                        dbc.Button(
                            [forward_label, html.I(className="bi bi-arrow-right ms-2")],
                            id="btn-forward",
                            color="primary",
                            disabled=not can_go_forward,
                            className="btn-lg",
                            style={
                                "display": "none" if not can_go_forward else "block"
                            },
                        )
                    ],
                    width="auto",
                    className="ms-auto",
                ),
            ],
            className="d-flex",
        )


class StepContent:
    """Contenido de cada paso con diseño optimizado."""

    @staticmethod
    def step_0_inicio():
        """Paso 0: Pantalla de inicio."""
        return dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                html.I(
                                    className="bi bi-heart-pulse-fill text-savia-primary",
                                    style={"fontSize": "3rem"},
                                ),
                                html.H2(
                                    "Sistema de Automatización RIPS",
                                    className="mt-3 mb-4",
                                ),
                            ],
                            className="text-center",
                        ),
                        html.P(
                            [
                                "Generación automatizada de reportes ",
                                html.Strong(
                                    "RIPS (Registros Individuales de Prestación de Servicios de Salud)"
                                ),
                            ],
                            className="lead text-center mb-4",
                        ),
                        html.Hr(),
                        # Características
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardBody(
                                                    [
                                                        html.I(
                                                            className="bi bi-file-text-fill text-savia-primary",
                                                            style={"fontSize": "2rem"},
                                                        ),
                                                        html.H5(
                                                            "Normativas",
                                                            className="mt-3",
                                                        ),
                                                        html.P(
                                                            "Resoluciones 3374/2000 y 2275/2023",
                                                            className="small text-muted",
                                                        ),
                                                    ],
                                                    className="text-center",
                                                )
                                            ],
                                            className="card-savia h-100",
                                        )
                                    ],
                                    md=3,
                                    className="mb-3",
                                ),
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardBody(
                                                    [
                                                        html.I(
                                                            className="bi bi-card-list text-savia-primary",
                                                            style={"fontSize": "2rem"},
                                                        ),
                                                        html.H5(
                                                            "Tipos RIPS",
                                                            className="mt-3",
                                                        ),
                                                        html.P(
                                                            "AC, AP, AH",
                                                            className="small text-muted",
                                                        ),
                                                    ],
                                                    className="text-center",
                                                )
                                            ],
                                            className="card-savia h-100",
                                        )
                                    ],
                                    md=3,
                                    className="mb-3",
                                ),
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardBody(
                                                    [
                                                        html.I(
                                                            className="bi bi-sliders text-savia-primary",
                                                            style={"fontSize": "2rem"},
                                                        ),
                                                        html.H5(
                                                            "Filtros Avanzados",
                                                            className="mt-3",
                                                        ),
                                                        html.P(
                                                            "Globales y específicos",
                                                            className="small text-muted",
                                                        ),
                                                    ],
                                                    className="text-center",
                                                )
                                            ],
                                            className="card-savia h-100",
                                        )
                                    ],
                                    md=3,
                                    className="mb-3",
                                ),
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardBody(
                                                    [
                                                        html.I(
                                                            className="bi bi-download text-savia-primary",
                                                            style={"fontSize": "2rem"},
                                                        ),
                                                        html.H5(
                                                            "Exportación CSV",
                                                            className="mt-3",
                                                        ),
                                                        html.P(
                                                            "Compatible con Excel",
                                                            className="small text-muted",
                                                        ),
                                                    ],
                                                    className="text-center",
                                                )
                                            ],
                                            className="card-savia h-100",
                                        )
                                    ],
                                    md=3,
                                    className="mb-3",
                                ),
                            ],
                            className="mb-4",
                        ),
                        html.Hr(),
                        dbc.Alert(
                            [
                                html.I(className="bi bi-info-circle-fill me-2"),
                                html.Strong("Datos Validados: "),
                                "Fuentes validadas con normalización automática según catálogos oficiales.",
                            ],
                            color="info",
                            className="alert-savia mb-0",
                        ),
                    ]
                )
            ],
            className="card-savia",
        )

    @staticmethod
    def step_1_normativa(selected_normativa: str = None):
        """Paso 1: Selección de normativa."""
        return dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.H4(
                            [
                                html.I(className="bi bi-file-text me-2"),
                                "Selección de Normativa",
                            ],
                            className="mb-4 text-savia-secondary",
                        ),
                        html.P(
                            "Seleccione la normativa para generar el reporte:",
                            className="mb-4",
                        ),
                        dbc.RadioItems(
                            id="radio-normativa",
                            options=[
                                {
                                    "label": dbc.Card(
                                        [
                                            dbc.CardBody(
                                                [
                                                    html.H5(
                                                        [
                                                            html.I(
                                                                className="bi bi-archive me-2"
                                                            ),
                                                            "Resolución 3374 de 2000",
                                                        ],
                                                        className="mb-3 text-savia-secondary",
                                                    ),
                                                    html.P(
                                                        [
                                                            html.Strong(
                                                                "Formato tradicional"
                                                            ),
                                                            html.Br(),
                                                            "Datos desde 2013",
                                                        ],
                                                        className="text-muted mb-0",
                                                    ),
                                                ],
                                                className="py-3",
                                            )
                                        ],
                                        className="card-savia selectable-card mb-3",
                                        style={
                                            "cursor": "pointer",
                                            "border": f"2px solid {'var(--savia-primary)' if selected_normativa == '3374' else 'transparent'}",
                                            "backgroundColor": (
                                                "var(--niagara-50)"
                                                if selected_normativa == "3374"
                                                else "white"
                                            ),
                                        },
                                    ),
                                    "value": "3374",
                                },
                                {
                                    "label": dbc.Card(
                                        [
                                            dbc.CardBody(
                                                [
                                                    html.H5(
                                                        [
                                                            html.I(
                                                                className="bi bi-stars me-2"
                                                            ),
                                                            "Resolución 2275 de 2023",
                                                        ],
                                                        className="mb-3 text-savia-secondary",
                                                    ),
                                                    html.P(
                                                        [
                                                            html.Strong(
                                                                "Nueva estructura"
                                                            ),
                                                            html.Br(),
                                                            "Datos desde 2025",
                                                        ],
                                                        className="text-muted mb-0",
                                                    ),
                                                ],
                                                className="py-3",
                                            )
                                        ],
                                        className="card-savia selectable-card mb-3",
                                        style={
                                            "cursor": "pointer",
                                            "border": f"2px solid {'var(--savia-primary)' if selected_normativa == '2275' else 'transparent'}",
                                            "backgroundColor": (
                                                "var(--niagara-50)"
                                                if selected_normativa == "2275"
                                                else "white"
                                            ),
                                        },
                                    ),
                                    "value": "2275",
                                },
                            ],
                            value=selected_normativa,
                        ),
                    ]
                )
            ],
            className="card-savia",
        )

    @staticmethod
    def step_2_tipos_rips(selected_tipo: str = None):
        """Paso 2: Selección de tipo RIPS."""
        return dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.H4(
                            [
                                html.I(className="bi bi-card-list me-2"),
                                "Selección de Tipo RIPS",
                            ],
                            className="mb-4 text-savia-secondary",
                        ),
                        html.P(
                            "Seleccione el tipo de RIPS a generar:", className="mb-3"
                        ),
                        dbc.Alert(
                            [
                                html.I(className="bi bi-info-circle-fill me-2"),
                                html.Strong("Optimización: "),
                                "Solo puede generar un tipo por consulta. Para múltiples tipos, ejecute consultas separadas.",
                            ],
                            color="info",
                            className="alert-savia mb-4",
                        ),
                        dbc.RadioItems(
                            id="radio-tipos-rips",
                            options=[
                                {
                                    "label": dbc.Card(
                                        [
                                            dbc.CardBody(
                                                [
                                                    html.H5(
                                                        [
                                                            html.I(
                                                                className="bi bi-clipboard2-pulse me-2"
                                                            ),
                                                            "AC - Consultas",
                                                        ],
                                                        className="mb-3 text-savia-secondary",
                                                    ),
                                                    html.P(
                                                        "Consultas médicas ambulatorias",
                                                        className="text-muted mb-0",
                                                    ),
                                                ],
                                                className="py-3",
                                            )
                                        ],
                                        className="card-savia selectable-card mb-3",
                                        style={
                                            "cursor": "pointer",
                                            "border": f"2px solid {'var(--savia-primary)' if selected_tipo == 'AC' else 'transparent'}",
                                            "backgroundColor": (
                                                "var(--niagara-50)"
                                                if selected_tipo == "AC"
                                                else "white"
                                            ),
                                        },
                                    ),
                                    "value": "AC",
                                },
                                {
                                    "label": dbc.Card(
                                        [
                                            dbc.CardBody(
                                                [
                                                    html.H5(
                                                        [
                                                            html.I(
                                                                className="bi bi-scissors me-2 text-muted"
                                                            ),
                                                            "AP - Procedimientos",
                                                        ],
                                                        className="mb-3 text-muted",
                                                    ),
                                                    html.P(
                                                        [
                                                            "Procedimientos realizados",
                                                            html.Br(),
                                                            dbc.Badge(
                                                                "Próximamente",
                                                                color="warning",
                                                                className="mt-2",
                                                            ),
                                                        ],
                                                        className="text-muted mb-0",
                                                    ),
                                                ],
                                                className="py-3",
                                            )
                                        ],
                                        className="card-savia mb-3",
                                        style={"opacity": "0.6"},
                                    ),
                                    "value": "AP",
                                    "disabled": True,
                                },
                                {
                                    "label": dbc.Card(
                                        [
                                            dbc.CardBody(
                                                [
                                                    html.H5(
                                                        [
                                                            html.I(
                                                                className="bi bi-hospital me-2 text-muted"
                                                            ),
                                                            "AH - Hospitalización",
                                                        ],
                                                        className="mb-3 text-muted",
                                                    ),
                                                    html.P(
                                                        [
                                                            "Hospitalizaciones",
                                                            html.Br(),
                                                            dbc.Badge(
                                                                "Próximamente",
                                                                color="warning",
                                                                className="mt-2",
                                                            ),
                                                        ],
                                                        className="text-muted mb-0",
                                                    ),
                                                ],
                                                className="py-3",
                                            )
                                        ],
                                        className="card-savia mb-3",
                                        style={"opacity": "0.6"},
                                    ),
                                    "value": "AH",
                                    "disabled": True,
                                },
                            ],
                            value=selected_tipo if selected_tipo else "AC",
                        ),
                    ]
                )
            ],
            className="card-savia",
        )


class ACStepContent:
    """Contenido del paso 3 para AC con layout responsive."""

    @staticmethod
    def step_3_configuracion_ac(normativa: str):
        """Paso 3: Configuración de consulta para AC."""
        return dbc.Row(
            [
                # Filtros globales
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    [
                                        html.I(className="bi bi-globe me-2"),
                                        "Filtros Globales",
                                    ],
                                    className="card-header-savia",
                                ),
                                dbc.CardBody(
                                    id="panel-filtros-globales",
                                    style={"position": "relative", "zIndex": "100"},
                                ),
                            ],
                            className="card-savia mb-3",
                        )
                    ],
                    lg=3,
                    md=12,
                    className="mb-3 mb-lg-0",
                ),
                # Filtros específicos + Columnas
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    [
                                        html.I(className="bi bi-sliders me-2"),
                                        "Filtros Específicos - AC",
                                    ],
                                    className="card-header-savia",
                                ),
                                dbc.CardBody(id="panel-filtros-especificos"),
                            ],
                            className="card-savia mb-3",
                        ),
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    [
                                        html.I(className="bi bi-table me-2"),
                                        "Columnas de Exportación",
                                    ],
                                    className="card-header-savia",
                                ),
                                dbc.CardBody(id="panel-columnas"),
                            ],
                            className="card-savia",
                        ),
                    ],
                    lg=6,
                    md=12,
                    className="mb-3 mb-lg-0",
                ),
                # Resumen + Acciones
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    [
                                        html.I(className="bi bi-card-checklist me-2"),
                                        "Resumen",
                                    ],
                                    className="card-header-savia",
                                ),
                                dbc.CardBody(id="panel-resumen"),
                            ],
                            className="card-savia mb-3",
                        ),
                        dbc.Card(
                            [dbc.CardBody(id="panel-acciones")], className="card-savia"
                        ),
                    ],
                    lg=3,
                    md=12,
                ),
            ]
        )
