# Build context: ./frontend
# docker build -f frontend/Dockerfile -t finguard-frontend ./frontend
FROM nginx:1.27-alpine

# Remove default site config
RUN rm /etc/nginx/conf.d/default.conf

# nginx official image auto-runs envsubst on /etc/nginx/templates/*.template
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# The single-page UI
COPY index.html /usr/share/nginx/html/index.html

# Default backend URL — override at runtime via -e BACKEND_URL=http://...
ENV BACKEND_URL=http://backend:5001

EXPOSE 80
