FROM nginx:1.27-alpine

RUN mkdir -p /var/cache/nginx && \
    chown -R nginx:nginx /var/cache/nginx

COPY nginx.vulnerable.conf /etc/nginx/conf.d/nginx.vulnerable.conf
COPY nginx.secure.conf /etc/nginx/conf.d/nginx.secure.conf
COPY entrypoint.sh /docker-entrypoint-lab.sh

RUN chmod +x /docker-entrypoint-lab.sh

EXPOSE 80

ENTRYPOINT ["/docker-entrypoint-lab.sh"]
