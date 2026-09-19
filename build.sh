#!/usr/bin/env bash
# exit on error
set -o errexit

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
elif [ -f "backend/requirements.txt" ]; then
    pip install -r backend/requirements.txt
fi

if [ -f "manage.py" ]; then
    python manage.py collectstatic --no-input
    python manage.py migrate
elif [ -f "backend/manage.py" ]; then
    cd backend
    python manage.py collectstatic --no-input
    python manage.py migrate
fi
