# ── Environment fingerprint (reproduced from local dev machine) ───────────────
#
#  Host OS  : macOS 14.6.1 (arm64 / Apple Silicon, Homebrew)
#  Node     : v25.8.1  (npm 11.11.0, ABI 141, V8 14.1.146.11, OpenSSL 3.6.1)
#  Lock     : package-lock.json v3  (npm 7+ format)
#  Bundler  : react-scripts 5.0.1 + webpack 5.106.2
#  Native   : fsevents (macOS-only — automatically skipped on Linux by npm)
#  Config   : no .nvmrc / .node-version / .npmrc / postcss.config.js present
#
#  Node 22 LTS (Jod) is the closest stable equivalent to local Node 25:
#    - ships npm 10.x  →  fully supports lockfileVersion 3
#    - webpack 5.x is compatible with Node 14-25; bundle output is identical
#    - Node 25 is a current (odd, non-LTS) release — not suitable for images
#
#  No NODE_OPTIONS=--openssl-legacy-provider is needed: that flag is only
#  required for webpack 4 (react-scripts ≤4). webpack 5 bundles the crypto
#  compat shim itself and works with any Node ≥ 14 OpenSSL provider.
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: build React ──────────────────────────────────────────────────────
FROM node:22-alpine AS builder

WORKDIR /app

# Copy manifests before source so this layer is cached between code-only changes
COPY package.json package-lock.json ./

# --no-audit / --no-fund match local npm 11 defaults (no network round-trips).
# fsevents (macOS-only native module) is automatically excluded on Linux.
RUN npm ci --no-audit --no-fund

# Copy only the source directories — never COPY . . without a .dockerignore:
# the host node_modules (399 MB) would overwrite the fresh install above.
COPY public ./public
COPY src    ./src

# CI=false  → react-scripts in CI mode converts ESLint warnings to hard errors;
#             local `npm run build` does not — this flag restores that parity.
# GENERATE_SOURCEMAP=false → source maps are not served from nginx; omitting
#             them halves build output size with zero runtime impact.
ENV CI=false \
    GENERATE_SOURCEMAP=false

RUN npm run build

# ── Stage 2: serve with nginx ─────────────────────────────────────────────────
FROM nginx:1.27-alpine

COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
