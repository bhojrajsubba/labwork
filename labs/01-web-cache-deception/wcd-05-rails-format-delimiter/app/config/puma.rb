# Bind explicitly to internal app port 5000 (do not read HOST PORT=8081 from .env)
bind "tcp://0.0.0.0:#{ENV.fetch('APP_PORT', 5000)}"
environment ENV.fetch("RAILS_ENV", "production")
workers 0
threads 1, 4
