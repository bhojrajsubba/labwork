#!/bin/sh
set -e

echo "[*] Initializing Nginx Origin Reverse Proxy (Lab 04: Cloudflare vs Origin Normalization)..."
echo "[*] Selected MODE from environment: ${MODE}"

if [ "${MODE}" = "secure" ]; then
    echo "[*] Applying SECURE Nginx Origin configuration (No trailing-slash URI normalization)"
    cp /etc/nginx/conf.d/nginx.secure.conf /etc/nginx/nginx.conf
else
    echo "[*] Applying VULNERABLE Nginx Origin configuration (Trailing-slash proxy_pass normalizes URIs)"
    cp /etc/nginx/conf.d/nginx.vulnerable.conf /etc/nginx/nginx.conf
fi

exec nginx -g "daemon off;"
