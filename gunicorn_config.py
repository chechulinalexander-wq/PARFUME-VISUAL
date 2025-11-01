"""
Gunicorn configuration for Perfume Visual Generator
Production setup for Ubuntu VPS
"""
import os
import multiprocessing

# Server socket
bind = "127.0.0.1:8080"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1  # Optimal for CPU-bound tasks
worker_class = "sync"
worker_connections = 1000
max_requests = 1000  # Restart workers after serving this many requests (prevents memory leaks)
max_requests_jitter = 50
timeout = 300  # Increased timeout for AI API calls (5 minutes)
keepalive = 5
graceful_timeout = 30

# Logging
accesslog = "/var/log/perfume-visual/access.log"
errorlog = "/var/log/perfume-visual/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "perfume-visual"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Server hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    print("=" * 70)
    print("Perfume Visual Generator - Starting Server")
    print("=" * 70)

def when_ready(server):
    """Called just after the server is started."""
    print(f"Server is ready. Listening on {bind}")
    print("=" * 70)

def on_exit(server):
    """Called just before exiting."""
    print("=" * 70)
    print("Perfume Visual Generator - Server stopped")
    print("=" * 70)

def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal."""
    print(f"Worker {worker.pid} received INT/QUIT signal")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    print(f"Worker {worker.pid} received ABORT signal")

