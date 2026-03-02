#!/bin/sh
set -e

echo ">>> Migratsiyalar ishga tushirilmoqda..."
python manage.py migrate --noinput

echo ">>> Static fayllar yig'ilmoqda..."
python manage.py collectstatic --noinput

echo ">>> Server ishga tushirilmoqda..."
exec "$@"
