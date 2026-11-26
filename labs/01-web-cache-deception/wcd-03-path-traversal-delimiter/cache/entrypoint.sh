#!/bin/sh
set -e

echo "[*] Initializing Nginx Cache Layer (Lab 03: Path Traversal Normalization)..."
echo "[*] Selected MODE from environment: ${MODE}"

if [ "${MODE}" = "secure" ]; then
    echo "[*] Applying SECURE Nginx configuration"
    cp /etc/nginx/conf.d/nginx.secure.conf /etc/nginx/nginx.conf
else
    echo "[*] Applying VULNERABLE Nginx configuration"
    cp /etc/nginx/conf.d/nginx.vulnerable.conf /etc/nginx/nginx.conf
fi

rm -rf /var/cache/nginx/*

exec nginx -g "daemon off;"
