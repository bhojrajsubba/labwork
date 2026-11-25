#!/bin/sh
set -e

echo "[*] Starting Nginx Cache Layer..."
echo "[*] Selected MODE: ${MODE:-vulnerable}"

if [ "${MODE}" = "secure" ]; then
    echo "[*] Applying SECURE Nginx configuration"
    cp /etc/nginx/conf.d/nginx.secure.conf /etc/nginx/nginx.conf
else
    echo "[*] Applying VULNERABLE Nginx configuration"
    cp /etc/nginx/conf.d/nginx.vulnerable.conf /etc/nginx/nginx.conf
fi

# Clean previous cache entries on container boot
rm -rf /var/cache/nginx/*

exec nginx -g "daemon off;"
