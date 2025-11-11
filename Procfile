release: python manage.py migrate --no-input

web: python manage.py collectstatic --no-input && gunicorn centre.wsgi:application --log-file -