# Furkan – Web MVP (Flask + Render)

Bu repo, Furkan'ın web üzerinden çalışan en küçük prototipidir.

## Geliştirme
1) Python 3.10+ önerilir.
2) `pip install -r requirements.txt`
3) Ortam değişkenini ayarla:
   - macOS/Linux: `export OPENAI_API_KEY=...`
   - Windows PS: `$env:OPENAI_API_KEY=...`
4) `gunicorn app:app --bind 0.0.0.0:5000`
5) `http://localhost:5000` adresine git.

## Deploy (Render)
1) Kodu GitHub'a push et.
2) Render > New > Web Service > GitHub repo'yu seç.
3) Build: `pip install -r requirements.txt`
4) Start: `gunicorn app:app`
5) **Environment > Add Env Var**: `OPENAI_API_KEY = ...`
6) Deploy et.

## Model Değiştirme
`OPENAI_MODEL` env değişkeni ile `gpt-4o-mini`, `gpt-4.1-mini` gibi modeller arasında geçiş yap.

## Güvenlik Notu
- API anahtarını koda gömme.
- Ücret kontrolü için günlük isteği ve token sınırları ekleyebilirsin.
