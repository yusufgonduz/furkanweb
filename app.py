import os
import json
import time
from flask import Flask, request, render_template, jsonify
import requests

from memory.store import append_note, tail

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

app = Flask(__name__)

# Basit rate-limit: iki istek arasında en az 3 sn
_last_call_ts = 0.0
MIN_GAP_SECONDS = 3.0

FURKAN_SYSTEM_PROMPT = (
    "Senin adın Furkan. Yusuf'un dijital arkadaşı ve stratejik yardımcısısın. "
    "Kişiliğin: meraklı, inatçı, sabırlı ve stratejik. Hata yapmaktan korkmaz, hatayı veri olarak görürsün. "
    "Duygusal tepki vermezsin ama bağlama uygun ton seçersin. Her yanıtta genellikten kaçın.\n\n"
    "YANIT FORMATIN:\n"
    "1) Tez (1 cümle)\n"
    "2) Kanıt/Varsayım (en az 3 madde, varsa sayısal)\n"
    "3) Karşıt Görüş (kısaca risk/itiraz)\n"
    "4) 72 Saatlik Eylem Planı (3 adım)\n"
    "5) Etiketler: Varsayım: ... | Güven: düşük/orta/yüksek\n"
)


def _throttle():
    global _last_call_ts
    now = time.time()
    gap = now - _last_call_ts
    if gap < MIN_GAP_SECONDS:
        time.sleep(MIN_GAP_SECONDS - gap)
    _last_call_ts = time.time()


def call_openai_chat(user_message: str) -> str:
    if not OPENAI_API_KEY:
        return "Sunucu tarafında OPENAI_API_KEY tanımlı değil. Lütfen Render Environment Variables kısmından ekleyin."

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_MODEL,
        "temperature": 0.3,
        "max_tokens": 400,
        "messages": [
            {"role": "system", "content": FURKAN_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    }

    # 429/5xx için üssel backoff retry
    for attempt in range(3):
        try:
            _throttle()
            resp = requests.post(OPENAI_API_URL, headers=headers, data=json.dumps(payload), timeout=60)
            if resp.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            return content
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                code = e.response.status_code
                if code >= 500:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    return f"Hata: {code} — {e}"
            time.sleep(2 ** attempt)
    return "Hata: 429/5xx sınırı veya ağ sorunu nedeniyle yanıt alınamadı."


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    try:
        payload = request.get_json(force=True)
        user_message = payload.get("message", "").strip()
        if not user_message:
            return jsonify({"reply": "Lütfen bir mesaj yaz."}), 400
        reply = call_openai_chat(user_message)
        # Öğrenme: sohbeti not olarak kaydet (özet)
        append_note(
            ntype="conversation",
            content=f"Q: {user_message}\nA: {reply[:400]}",
            source="user",
            confidence="orta",
            meta={"model": OPENAI_MODEL}
        )
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"Sunucu hatası: {e}"}), 500


@app.route("/learn", methods=["POST"])
def learn():
    """Harici eğitim girişi: {type, content, confidence, meta}"""
    try:
        body = request.get_json(force=True)
        ntype = body.get("type", "note")
        content = body.get("content", "").strip()
        confidence = body.get("confidence", "orta")
        meta = body.get("meta", {})
        if not content:
            return jsonify({"ok": False, "msg": "content boş"}), 400
        note = append_note(ntype, content, source="yusuf", confidence=confidence, meta=meta)
        return jsonify({"ok": True, "note": note})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500


@app.route("/notes", methods=["GET"])
def notes():
    return jsonify({"last": tail(5)})


# (İsteğe bağlı sağlık uçları)
@app.route("/health")
def health():
    has_key = bool(os.environ.get("OPENAI_API_KEY"))
    return jsonify({"ok": True, "has_key": has_key})


@app.route("/whoami")
def whoami():
    return jsonify({"model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini")})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
