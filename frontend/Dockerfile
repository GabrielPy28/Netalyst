# Build estático + Nginx: proxy /api → backend.
# Origen del API por env NETALYST_API_ORIGIN (ver nginx/templates/default.conf.template).
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG VITE_API_BASE=/api/v1
ENV VITE_API_BASE=$VITE_API_BASE
RUN npm run build

FROM nginx:1.27-alpine
ENV NETALYST_API_ORIGIN=http://api:8000
COPY nginx/templates/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
