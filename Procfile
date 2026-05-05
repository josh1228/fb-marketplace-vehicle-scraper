release: playwright install --with-deps chromium
web: gunicorn -w 2 -k uvicorn.workers.UvicornWorker main:app
