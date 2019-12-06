web: gunicorn --worker-class gevent vpuu.wsgi:application -t 300 --log-file -
worker: python manage.py qcluster