# RIPS Automation System

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)
![Dash](https://img.shields.io/badge/Dash-3.3.0-purple?logo=plotly)
![License](https://img.shields.io/badge/License-MIT-green)

Sistema de generación autónoma de reportes RIPS (Registros Individuales de Prestación de Servicios de Salud) para usuarios no técnicos en Savia Salud EPS. Transforma procesos manuales de 2–5 días en consultas autoservicio de minutos.

## ✨ Características

- **Soporte dual de normativas**: Resolución 3374/2000 (legacy) y 2275/2023 (moderna)
- **Tres tipos de reportes**: AC (Consultas), AP (Procedimientos), AH (Hospitalización)
- **Fuentes integradas**: 4 bases de datos (MySQL/PostgreSQL) con enrutamiento automático por fecha
- **ETL multi-conexión**: Consolidación, estandarización y deduplicación sin pérdida de información
- **Filtros avanzados**: 2 modos de entrada (lista/archivo), 3 categorías (múltiples/categóricas/rango)
- **Exportación estándar**: CSV UTF-8 BOM con formato exigido por entidades reguladoras
- **Arquitectura MVC limpia**: Separación clara entre presentación, lógica y datos

## 🛠️ Requisitos

- Python 3.9+
- Variables de entorno configuradas (ver `.env.example`)
- Acceso a las 4 bases de datos descritas en la documentación

## 📦 Instalación

```bash
git clone <repo-url>
cd rips-automation
python -m venv venv
source venv/bin/activate  # Linux/macOS
# o venv\Scripts\activate en Windows
pip install -r requirements.txt
cp .env.example .env
# Editar .env con credenciales reales
python app.py
```

## 🧪 Pruebas de Conectividad

Valida acceso a fuentes de datos antes del uso completo:

```bash
python tests/test_connections.py
```

## 📁 Estructura actual del proyecto


```lang
├── assets
│   ├── loading.js
│   └── styles.css
├── callbacks
│   └── filter_callbacks.py
├── config
│   ├── __init__.py
│   ├── database.py
│   └── settings.py
├── controllers
│   ├── __init__.py
│   └── ac_controller.py
├── models
│   ├── __init__.py
│   ├── ac_model.py
│   └── base.py
├── services
│   ├── __init__.py
│   ├── data_processor.py
│   └── query_builder.py
├── tests
│   └── test_connections.py
├── utils
│   ├── __init__.py
│   ├── catalogs.py
│   ├── file_handler.py
│   └── validators.py
├── views
│   ├── __init__.py
│   ├── ac_view.py
│   ├── components.py
│   └── layout.py
├── .env.example
├── .gitignore
├── app.py
└── requirements.txt
```

- `app.py`: Punto de entrada (Dash)
- `config/`: Conexiones y configuración global
- `models/`: Mapeos y reglas por normativa
- `controllers/`: Orquestación de operaciones
- `services/`: Lógica de construcción y procesamiento de datos
- `views/` + `callbacks/`: Interfaz y manejo de eventos
- `utils/`: Validación, normalización y manejo de archivos


## 📜 Licencia

MIT – uso interno autorizado para Savia Salud EPS.