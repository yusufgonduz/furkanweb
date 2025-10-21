import os
import json
from flask import Flask, request, render_template, jsonify
import requests

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"  # Stabil uç nokta
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")  # İstersen Render'da değiştirebilirsin

app = Flask(__name__)

# ——— Furkan çekirdek kişilik (sistem mesajı) ———
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
        "messages": [
            {"role": "system", "content": FURKAN_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    }

    try:
        resp = requests.post(OPENAI_API_URL, headers=headers, data=json.dumps(payload), timeout=60)
        resp.raise_for_status()
        data = resp.json()
        # Standart Chat Completions cevabı
        content = data["choices"][0]["message"]["content"].strip()
        return content
    except Exception as e:
        return f"Hata: {e} — Yanıt alınamadı."


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
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"Sunucu hatası: {e}"}), 500


if __name__ == "__main__":
    # Lokal çalıştırma (Render'da gunicorn kullanacağız)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
