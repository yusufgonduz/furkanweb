import os, json, datetime, threading

_LOCK = threading.Lock()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "notes.json")

SCHEMA_VERSION = 1

DEFAULT_DOC = {
    "schema": SCHEMA_VERSION,
    "notes": []  # {t, type, content, source, confidence, meta}
}

def _now_iso():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure_file():
    if not os.path.exists(DATA_PATH):
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_DOC, f, ensure_ascii=False, indent=2)


def load_all():
    _ensure_file()
    with _LOCK:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)


def append_note(ntype: str, content: str, source: str = "system", confidence: str = "orta", meta: dict | None = None):
    _ensure_file()
    with _LOCK:
        doc = load_all()
        note = {
            "t": _now_iso(),
            "type": ntype,
            "content": content,
            "source": source,
            "confidence": confidence,
            "meta": meta or {},
        }
        doc["notes"].append(note)
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
        return note


def tail(n: int = 5):
    doc = load_all()
    return list(doc.get("notes", []))[-n:]
