# Mebel360 Hisobchi — Server 2.0

Bu versiyada eski hisoblash, Pro Konstruktor, Studio 3D va 2D-PLACE funksiyalari saqlangan. Qo‘shimcha ravishda server bazasi, login, backup, CBU kursi, ombor va Mebel360 ERP ulanishi qo‘shildi.

## Lokal ishga tushirish
1. `start.bat` ni bosing.
2. Birinchi standart kirish: `admin` / `Mebel360-360`.
3. Kirgandan keyin `Server / ERP` bo‘limidan parolni albatta almashtiring.

## Render uchun
Endi Static Site emas, **Web Service** kerak.
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn server_app:app --workers 1 --threads 4 --timeout 120`
- Python: 3.12.8

Environment:
- `SECRET_KEY` — uzun tasodifiy maxfiy qiymat
- `ADMIN_USER=admin`
- `ADMIN_PASSWORD` — kuchli parol
- `DATABASE_URL` — Render PostgreSQL manzili (tavsiya qilinadi)
- `OPENAI_API_KEY` — AI uchun, ixtiyoriy
- `OPENAI_MODEL=gpt-5-mini` — ixtiyoriy
- `MEBEL360_ERP_URL` — Mebel360 ERP manzili, masalan `https://pharm-mebel.onrender.com`
- `MEBEL360_ERP_TOKEN` — Hisobchi va ERP da bir xil maxfiy token

Agar `DATABASE_URL` qo‘yilmasa SQLite ishlaydi. Render’da deploylar orasida ma’lumot saqlanishi uchun PostgreSQL tavsiya qilinadi.

## Yangi funksiyalar
- Login va rollar
- Loyihalarni serverga avtomatik saqlash
- Material/furnitura/qoldiq/navbatni 30 soniyada sinxronlash
- Har saqlashdan oldin avtomatik snapshot
- JSON backup yuklab olish
- CBU kursi (USD/EUR/RUB/CNY) va kurs bo‘yicha LMDF narxini hisoblash
- Ombor materiallari va mavjud qoldiq
- Mebel360 ERP ga loyiha yuborish va navbat
- O‘lcham/bo‘lim bo‘yicha server validatsiyasi
- AI va 2D-PLACE API larini login bilan himoyalash

## ERP ulanishi
ERP zip ichidagi `app.py` ga `/api/hisobchi/import` endpointi qo‘shilgan alohida ERP tayyor zip ham beriladi. Hisobchi va ERP Render Environment ichida `MEBEL360_ERP_TOKEN` bir xil bo‘lishi kerak.
