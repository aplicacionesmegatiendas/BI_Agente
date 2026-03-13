from mcp.server.fastmcp import FastMCP

from domain_loader import load_all_docs
from prompts import DBA_AGENT_PROMPT

mcp = FastMCP("ventas-dba-mcp", json_response=True)

DOCS = load_all_docs()


# =========================
# Resources
# =========================

@mcp.resource("docs://protocolo_conversacional")
def protocolo_conversacional() -> str:
    return DOCS["protocolo_conversacional"]


@mcp.resource("docs://reglas")
def reglas() -> str:
    return DOCS["reglas"]


@mcp.resource("docs://db_config_docs")
def db_config_docs() -> str:
    return DOCS["db_config_docs"]


@mcp.resource("docs://contexto_dba")
def contexto_dba() -> str:
    return "\n\n".join([
        "=== PROTOCOLO ===",
        DOCS["protocolo_conversacional"],
        "=== REGLAS ===",
        DOCS["reglas"],
        "=== DB CONFIG ===",
        DOCS["db_config_docs"],
    ])


# =========================
# Prompt
# =========================

@mcp.prompt()
def dba_request_prompt(user_request: str) -> str:
    return f"""
{DBA_AGENT_PROMPT}

Contexto del sistema:
{DOCS["protocolo_conversacional"]}

Solicitud del usuario:
{user_request}
"""


# =========================
# Tools
# =========================

@mcp.tool()
def validate_report_request(
    user_request: str,
    time_range: str | None = None,
    company_id: int | None = None,
    dimensions: list[str] | None = None
) -> dict:
    missing = []

    if not time_range:
        missing.append({
            "name": "time_range",
            "why": "El rango de fechas es obligatorio para construir la consulta.",
            "example": "2026-01-01 a 2026-01-31"
        })

    if not company_id:
        missing.append({
            "name": "company_id",
            "why": "Se recomienda identificar la compañía objetivo.",
            "example": "1"
        })

    if missing:
        return {
            "type": "MISSING_PARAMS",
            "payload": {
                "missing": missing,
                "questions": [
                    "¿Cuál es el rango de fechas?",
                    "¿Cuál es la compañía?"
                ],
                "defaults_if_no_answer": [],
                "notes": [
                    "Validación mínima del agente DBA."
                ]
            }
        }

    return {
        "type": "OK",
        "payload": {
            "message": "Solicitud válida para pasar a construcción de SQL."
        }
    }


@mcp.tool()
def resolve_dimension_value(
    dimension_name: str,
    search_text: str
) -> dict:
    return {
        "type": "OK",
        "payload": {
            "dimension_name": dimension_name,
            "search_text": search_text,
            "matches": [],
            "notes": [
                "MVP: resolución pendiente contra catálogos reales."
            ]
        }
    }


@mcp.tool()
def build_sql_query(
    user_request: str,
    kpi_id: str,
    time_range: str,
    company_id: int,
    dimensions: list[str] | None = None
) -> dict:
    dims = dimensions or []

    group_by = ""
    select_dims = ""

    if "familia" in dims:
        select_dims = "d.familia,\n    "
        group_by = "\nGROUP BY d.familia"

    sql = f"""
SELECT
    {select_dims}SUM(f.vr_vta_sin_iva_pesos) AS ventas
FROM F_ventas f
LEFT JOIN D_Item d
    ON f.sk_item = d.sk_item
LEFT JOIN D_Geografia g
    ON f.sk_geografia = g.sk_geografia
WHERE g.id_cia = @company_id
  AND f.fecha_dcto BETWEEN @start_date AND @end_date
{group_by}
""".strip()

    start_date, end_date = [x.strip() for x in time_range.split(" a ", 1)]

    return {
        "type": "SQL_RESULT",
        "payload": {
            "sql": sql,
            "params": [
                {"name": "company_id", "type": "int", "example": str(company_id)},
                {"name": "start_date", "type": "date", "example": start_date},
                {"name": "end_date", "type": "date", "example": end_date},
            ],
            "columns": (
                [{"name": "familia", "type": "string"}] if "familia" in dims else []
            ) + [{"name": "ventas", "type": "decimal"}],
            "grain": dims,
            "mode": "AGGREGATED",
            "notes": [
                "SQL de ejemplo para MVP.",
                "Usa solo SELECT.",
                "Join por surrogate keys."
            ]
        }
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

    