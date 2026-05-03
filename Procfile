release: playwright install chromium
web: gunicorn -w 2 -k uvicorn.workers.UvicornWorker main:app
