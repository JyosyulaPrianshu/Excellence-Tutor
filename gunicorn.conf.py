# Gunicorn configuration file for Render
# Reference: https://docs.gunicorn.org/en/stable/configure.html#configuration-file

workers = 1  # Reduced workers for Render's free tier
worker_class = 'gthread'
threads = 2  # 2 threads per worker
timeout = 120  # 2 minutes timeout
worker_tmp_dir = '/dev/shm'  # Use shared memory for worker temp files
max_requests = 1000  # Restart workers after this many requests
max_requests_jitter = 50  # Random jitter to prevent all workers restarting at once

# Logging configuration
accesslog = '-'  # Log to stdout
errorlog = '-'   # Log errors to stdout
loglevel = 'info'

# Preload the application to save memory
preload_app = True
