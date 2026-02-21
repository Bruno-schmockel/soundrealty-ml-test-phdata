"""Gunicorn configuration for Sound Realty Prediction API.

This config file can be used as:
    gunicorn -c gunicorn_config.py src.api.main:app
"""

# Server Configuration
bind = "0.0.0.0:8000"
backlog = 2048
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 60
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "sound-realty-api"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None
ssl_version = None
cert_reqs = None
ca_certs = None
suppress_ragged_eofs = True
do_handshake_on_connect = True
ciphers = None

# Application
preload_app = False
max_requests = 1000
max_requests_jitter = 50

# Server hooks (optional callbacks)
def on_starting(server):
    """Called just before the master process is initialized."""
    print("=== Sound Realty Prediction API Starting ===")
    print("Workers: 4")
    print("Worker class: uvicorn.workers.UvicornWorker")
    print("Bind: 0.0.0.0:8000")
    print("Documentation: http://localhost:8000/docs")

def when_ready(server):
    """Called just after the server is started."""
    print("===== Server is Ready =====")
    print("API is ready to accept requests")

def on_exit(server):
    """Called just before exiting Gunicorn."""
    print("=== Sound Realty Prediction API Stopped ===")
