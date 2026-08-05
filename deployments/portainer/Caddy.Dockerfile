# syntax=docker/dockerfile:1.7

FROM caddy:2.11.4-alpine

COPY deployments/portainer/Caddyfile /etc/caddy/Caddyfile