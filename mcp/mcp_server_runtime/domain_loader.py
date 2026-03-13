from pathlib import Path

BASE_DIR = Path(__file__).parent
DOCS_DIR = BASE_DIR / "docs"


def read_text_file(filename: str) -> str:
    path = DOCS_DIR / filename
    return path.read_text(encoding="utf-8")


def load_all_docs() -> dict:
    return {
        "protocolo_conversacional": read_text_file("protocolo_conversacional.txt"),
        "reglas": read_text_file("reglas.txt"),
        "db_config_docs": read_text_file("db_config_docs.txt"),
    }