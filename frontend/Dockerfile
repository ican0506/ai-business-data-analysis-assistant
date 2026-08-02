FROM docker.m.daocloud.io/library/node:22-alpine AS build
WORKDIR /app
COPY frontend/vue-app/package*.json ./
RUN npm ci
COPY frontend/vue-app ./
RUN npm run build

FROM nginx:1.27-alpine
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
