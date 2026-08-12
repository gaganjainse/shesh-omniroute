# shesh-omniroute — build the OmniRoute gateway image from our fork.
# Build: podman build -f Containerfile -t localhost/shesh-omniroute:latest .
# (or: shesh-omniroute build)

FROM docker.io/node:20-alpine AS build
RUN apk add --no-cache git
ARG OMNIROUTE_REPO=https://github.com/gaganjainse/OmniRoute.git
ARG OMNIROUTE_REF=release/v3.8.50
RUN git clone --depth 1 --branch "$OMNIROUTE_REF" "$OMNIROUTE_REPO" /app
WORKDIR /app
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund
RUN npm run build

FROM docker.io/node:20-alpine
ENV NODE_ENV=production \
    PORT=20128 \
    HOST=0.0.0.0
WORKDIR /app
COPY --from=build /app ./
EXPOSE 20128
# Gateway data (sqlite, routes) persists in /data via volume from the wrapper CLI.
VOLUME ["/data"]
ENV OMNIROUTE_DATA_DIR=/data
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1:20128/v1/models >/dev/null 2>&1 || exit 1
CMD ["npm", "start"]
