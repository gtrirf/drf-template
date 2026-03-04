# Django REST Framework Template

Production-ready Django REST API template. Foydalanuvchi autentifikatsiyasi, rol tizimi, JWT, email OTP, Redis cache va Docker bilan to'liq sozlangan.

---

## Tarkib

- [Xususiyatlar](#xususiyatlar)
- [Texnologiyalar](#texnologiyalar)
- [Loyiha tuzilmasi](#loyiha-tuzilmasi)
- [Boshlash](#boshlash)
  - [1. Reponi klonlash](#1-reponi-klonlash)
  - [2. `.env` faylini sozlash](#2-env-faylini-sozlash)
  - [3a. Local ishga tushirish](#3a-local-ishga-tushirish)
  - [3b. Docker bilan ishga tushirish](#3b-docker-bilan-ishga-tushirish)
- [API endpointlari](#api-endpointlari)
- [Rol tizimi](#rol-tizimi)
- [JWT tokenlar](#jwt-tokenlar)
- [Yangi app qo'shish](#yangi-app-qoshish)
- [Environment o'zgaruvchilar](#environment-ozgaruvchilar)

---

## Xususiyatlar

- **3 qadam registratsiya**: Email OTP tasdiqlash → Profil to'ldirish → Parol o'rnatish
- **JWT autentifikatsiya**: Access (15 daqiqa) + Refresh (1 kun) tokenlar, token blacklist
- **Rol tizimi**: `guest`, `user`, `admin`, `superadmin`
- **Parol tiklash**: Email orqali OTP bilan
- **Redis cache**: OTP kodlarni va sessiyalarni saqlash uchun
- **Throttling**: Anonimlar — 10/daqiqa, foydalanuvchilar — 100/daqiqa
- **Swagger UI**: `/api/schema/swagger-ui/` manzilida
- **Logging**: Rotating file logs (`logs/django.log`, `logs/errors.log`)
- **Docker**: PostgreSQL + Redis + Nginx + Gunicorn
- **CORS** sozlangan

---

## Texnologiyalar

| Kutubxona | Versiya | Maqsad |
|---|---|---|
| Django | 6.0.2 | Asosiy framework |
| djangorestframework | 3.16.1 | REST API |
| djangorestframework-simplejwt | 5.5.1 | JWT autentifikatsiya |
| drf-spectacular | 0.29.0 | Swagger/OpenAPI |
| django-environ | 0.13.0 | `.env` fayl o'qish |
| django-cors-headers | 4.9.0 | CORS |
| django-redis | 5.4.0 | Redis cache |
| psycopg2-binary | 2.9.10 | PostgreSQL |
| Pillow | 12.1.1 | Rasm yuklash |
| gunicorn | 25.1.0 | WSGI server |

---

## Loyiha tuzilmasi

```
django-template/
├── apps/
│   └── users/              # Foydalanuvchilar ilovasi
│       ├── models.py       # CustomUser, UserRole
│       ├── views.py        # Barcha API viewlar
│       ├── serializers.py  # Serializerlar
│       ├── urls.py         # URL marshrutlar
│       ├── permissions.py  # IsRoleAllowed permission
│       └── utils.py        # OTP, email yordamchi funksiyalar
├── config/
│   ├── settings.py         # Asosiy sozlamalar
│   ├── urls.py             # Root URL
│   └── wsgi.py
├── templates/              # HTML shablonlar (email uchun)
├── nginx/                  # Nginx konfiguratsiyasi
├── logs/                   # Log fayllar (avtomatik yaratiladi)
├── media/                  # Yuklangan fayllar
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh
├── requirements.txt
├── generate_key.py         # SECRET_KEY generator
└── .env.example
```

---

## Boshlash

### 1. Reponi klonlash

```bash
git clone <repo-url>
cd django-template
```

### 2. `.env` faylini sozlash

```bash
cp .env.example .env
```

`.env` faylini oching va quyidagi qiymatlarga o'zgartiring:

```env
# Django uchun yangi SECRET_KEY yarating:
# python generate_key.py
SECRET_KEY=your-secret-key-here
DEBUG=True

# Email sozlamalar (Gmail uchun App Password kerak)
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

**Gmail App Password olish:** Google Account → Security → 2-Step Verification → App passwords

---

### 3a. Local ishga tushirish

```bash
# Virtual muhit yaratish
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# Kerakli paketlarni o'rnatish
pip install -r requirements.txt

# Ma'lumotlar bazasini sozlash (default: SQLite)
python manage.py migrate

# Superuser yaratish
python manage.py createsuperuser

# Serverni ishga tushirish
python manage.py runserver
```

Server `http://localhost:8000` manzilida ishga tushadi.

> **Eslatma:** Local rejimda `USE_POSTGRES=False` bo'lsa SQLite ishlatiladi. Redis kerak bo'lmasa, `CACHES` ni `django.core.cache.backends.locmem.LocMemCache` ga o'zgartiring.

---

### 3b. Docker bilan ishga tushirish

```bash
# .env faylida quyidagini o'zgartiring:
# USE_POSTGRES=True
# DB_HOST=db
# REDIS_URL=redis://redis:6379/0

docker compose up --build
```

Servislar:
- **API**: `http://localhost:8001`
- **Swagger UI**: `http://localhost:8001/api/schema/swagger-ui/`
- **Admin panel**: `http://localhost:8001/admin/`

Docker ichida superuser yaratish:

```bash
docker compose exec backend python manage.py createsuperuser
```

---

## API endpointlari

### Registratsiya (3 qadam)

| Method | URL | Tavsif | Auth |
|---|---|---|---|
| POST | `/auth/register/send-otp/` | 1a: Emailga OTP yuborish | Yo'q |
| POST | `/auth/register/verify/` | 1b: OTP tasdiqlash, hisob yaratish | Yo'q |
| POST | `/auth/register/` | 2: Profil to'ldirish (ixtiyoriy) | Bearer token |
| POST | `/auth/register/set-password/` | 3: Doimiy parol o'rnatish | Bearer token |

**Registratsiya jarayoni:**

```
1. POST /auth/register/send-otp/    → { "email": "user@example.com" }
2. POST /auth/register/verify/      → { "email": "...", "code": "123456" }
   ← { access, refresh, user }  (bu tokenlarni saqlang!)
3. POST /auth/register/             → { "first_name": "...", "username": "..." }
   Authorization: Bearer <access>
4. POST /auth/register/set-password/ → { "new_password": "...", "confirm_password": "..." }
   Authorization: Bearer <access>
```

### Autentifikatsiya

| Method | URL | Tavsif | Auth |
|---|---|---|---|
| POST | `/auth/login/` | Kirish (access + refresh token) | Yo'q |
| POST | `/auth/logout/` | Chiqish (refresh tokenni blacklistga) | Bearer token |
| POST | `/auth/token/refresh/` | Access tokenni yangilash | Yo'q |

### Parol

| Method | URL | Tavsif | Auth |
|---|---|---|---|
| POST | `/auth/change-password/` | Parolni o'zgartirish | Bearer token |
| POST | `/auth/forgot-password/` | Parolni tiklash — OTP yuborish | Yo'q |
| POST | `/auth/forgot-password/verify/` | OTP tasdiqlash + yangi parol | Yo'q |

### Profil

| Method | URL | Tavsif | Auth |
|---|---|---|---|
| GET | `/users/me/` | O'z profilini ko'rish | Bearer token |
| PATCH | `/users/me/` | Profilni yangilash | Bearer token |

### Admin (faqat `admin` / `superadmin` rollari)

| Method | URL | Tavsif |
|---|---|---|
| GET | `/users/` | Barcha foydalanuvchilar ro'yxati |
| GET | `/users/<id>/` | Foydalanuvchi ma'lumotlari |
| PATCH | `/users/<id>/` | Foydalanuvchini tahrirlash |
| DELETE | `/users/<id>/` | Foydalanuvchini o'chirish |

### API hujjatlari

| URL | Tavsif |
|---|---|
| `/api/schema/swagger-ui/` | Swagger UI |
| `/api/schema/redoc/` | ReDoc |
| `/api/schema/` | OpenAPI schema (JSON/YAML) |

---

## Rol tizimi

| Rol | Tavsif |
|---|---|
| `guest` | Registratsiyadan o'tib, parol o'rnatmagan foydalanuvchi |
| `user` | Registratsiyani to'liq yakunlagan foydalanuvchi |
| `admin` | Barcha foydalanuvchilarni boshqarishi mumkin |
| `superadmin` | To'liq huquqlar (Django superuser) |

`IsRoleAllowed` permissionidan foydalanish:

```python
from apps.users.permissions import IsRoleAllowed
from apps.users.models import UserRole

class MyView(APIView):
    permission_classes = [IsAuthenticated, IsRoleAllowed]
    allowed_roles = [UserRole.ADMIN, UserRole.SUPERADMIN]
```

---

## JWT tokenlar

- **Access token**: 15 daqiqa amal qiladi
- **Refresh token**: 1 kun amal qiladi
- **Token rotation**: Har yangilanishda refresh token o'zgaradi
- **Blacklist**: Logout bo'lganda refresh token blacklistga qo'shiladi

Swagger yoki Postman da ishlatish:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Yangi app qo'shish

```bash
# 1. apps/ papkasida yangi app yarating
mkdir apps/products
python manage.py startapp products apps/products

# 2. apps/products/apps.py ichida nomni to'g'rilang:
#    name = 'apps.products'

# 3. config/settings.py ga qo'shing:
LOCAL_APPS = [
    "apps.users",
    "apps.products",   # ← yangi app
]

# 4. URL larni ulang (config/urls.py):
#    path('', include('apps.products.urls')),
```

---

## Environment o'zgaruvchilar

| O'zgaruvchi | Tavsif | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key (majburiy) | — |
| `DEBUG` | Debug rejim | `False` |
| `ALLOWED_HOSTS` | Ruxsat etilgan hostlar | `[]` |
| `USE_POSTGRES` | PostgreSQL ishlatish | `False` (SQLite) |
| `DB_NAME` | PostgreSQL bazasi nomi | `django_db` |
| `DB_USER` | PostgreSQL foydalanuvchi | `postgres` |
| `DB_PASSWORD` | PostgreSQL parol | — |
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `REDIS_URL` | Redis URL | `redis://localhost:6379/0` |
| `EMAIL_HOST_USER` | Gmail manzil (majburiy) | — |
| `EMAIL_HOST_PASSWORD` | Gmail App Password (majburiy) | — |
| `CORS_ALLOWED_ORIGINS` | CORS ruxsat etilgan originlar | `[]` |
| `CORS_ALLOW_CREDENTIALS` | CORS credentials | `False` |

---

## Foydali buyruqlar

```bash
# Yangi SECRET_KEY yaratish
python generate_key.py

# Migratsiyalarni yaratish
python manage.py makemigrations

# Migratsiyalarni qo'llash
python manage.py migrate

# Superuser yaratish
python manage.py createsuperuser

# Static fayllarni yig'ish
python manage.py collectstatic

# Docker loglarini ko'rish
docker compose logs -f backend
```
