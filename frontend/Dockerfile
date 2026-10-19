# syntax=docker/dockerfile:1
# Imagen del frontend (C-08, design F14). Contexto de construcción: frontend/.
# Bases fijadas por etiqueta y digest (D144): node 24.21.0-bookworm-slim (último push 2026-10-06)
# y nginx-unprivileged 1.30.4-alpine (último push 2026-09-14).
ARG NODE_IMAGE=node:24.21.0-bookworm-slim@sha256:d6aa754f16b3197301076f047b5def2f02ea1dbbc2ca920407d46d7ec7f87b20
ARG NGINX_IMAGE=nginxinc/nginx-unprivileged:1.30.4-alpine@sha256:adf5042a17f4ecdd200c595fa9ffd1be37efb18f89a830bd1a00e4ab4d59d42c

FROM ${NODE_IMAGE} AS construccion
WORKDIR /app
# Solo el manifiesto, para aprovechar la caché de capas.
COPY package.json package-lock.json .npmrc ./
RUN npm ci
COPY . .
# tsc --noEmit && vite build. Los tests no corren en la imagen: corren en la suite.
RUN npm run build

FROM ${NGINX_IMAGE} AS servidor
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=construccion /app/dist /usr/share/nginx/html
# La imagen ya corre como el usuario sin privilegios nginx (uid 101) y escucha en 8080.
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=5 \
    CMD ["wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080/"]
