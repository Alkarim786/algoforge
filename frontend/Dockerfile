# Production only: builds the static site and serves it with Caddy, which also terminates HTTPS and proxies
# /api to the FastAPI service. Development uses the Vite dev server from docker-compose.yml instead.
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
COPY scripts ./scripts
# postinstall copies Monaco into public/monaco, so the editor is served from our own origin.
RUN npm ci
COPY . .
RUN npm run build

FROM caddy:2.8-alpine
COPY --from=build /app/dist /srv
COPY Caddyfile /etc/caddy/Caddyfile
