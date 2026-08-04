# syntax=docker/dockerfile:1.7

FROM node:22.23.2-alpine3.23@sha256:46825fbbd4e996a78b7a2cdc08d75e38a5a505bdab95dcda55605359bf124bc6 AS dependencies

ENV COREPACK_HOME=/corepack \
    PNPM_HOME=/pnpm \
    PATH=/pnpm:$PATH

RUN npm install --global corepack@0.35.0 \
    && corepack enable

WORKDIR /workspace
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY frontend/package.json frontend/package.json
RUN --mount=type=cache,id=pnpm,target=/pnpm/store \
    corepack pnpm config set store-dir /pnpm/store \
    && corepack pnpm install --frozen-lockfile --ignore-scripts

FROM dependencies AS build

ENV NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production

COPY frontend frontend
RUN corepack pnpm --dir frontend build \
    && mkdir -p /out/frontend/frontend/.next \
    && cp -R frontend/.next/standalone/. /out/frontend/ \
    && cp -R frontend/.next/static /out/frontend/frontend/.next/static

FROM node:22.23.2-alpine3.23@sha256:46825fbbd4e996a78b7a2cdc08d75e38a5a505bdab95dcda55605359bf124bc6 AS runtime

ENV HOSTNAME=0.0.0.0 \
    NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production \
    PORT=3000

RUN rm -rf /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/corepack \
    && rm -f /usr/local/bin/npm /usr/local/bin/npx /usr/local/bin/corepack /usr/local/bin/pnpm /usr/local/bin/pnpx /usr/local/bin/yarn /usr/local/bin/yarnpkg \
    && addgroup --gid 10001 app \
    && adduser --uid 10001 --ingroup app --disabled-password --no-create-home --shell /sbin/nologin app \
    && mkdir -p /app/frontend/.next/cache \
    && chown -R app:app /app

WORKDIR /app
COPY --from=build --chown=10001:10001 /out/frontend/ ./

USER 10001:10001
EXPOSE 3000

HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=6 \
    CMD ["node", "-e", "fetch('http://127.0.0.1:3000/').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"]

CMD ["node", "frontend/server.js"]
