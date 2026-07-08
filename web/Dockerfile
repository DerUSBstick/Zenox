# ── Build stage ──────────────────────────────────────────────────────────────
FROM node:20-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ── Serve stage ───────────────────────────────────────────────────────────────
FROM nginx:alpine

# envsubst lives in gettext (pre-installed in nginx:alpine, but ensure it's there)
RUN apk add --no-cache gettext

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy built SPA
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx template — $BOT_UPSTREAM is substituted at container start
COPY nginx.conf.template /etc/nginx/nginx.conf.template

# Substitute only $BOT_UPSTREAM; leave nginx's own $uri, $host, etc. untouched
CMD ["/bin/sh", "-c", \
     "envsubst '$BOT_UPSTREAM' < /etc/nginx/nginx.conf.template \
      > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
