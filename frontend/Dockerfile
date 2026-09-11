FROM node:20-alpine AS build

WORKDIR /app
RUN corepack enable

COPY package.json yarn.lock ./
# yarn.lock predates the lucide-react declaration. Keep existing locked resolutions and
# resolve the one missing package without mutating the build context.
RUN yarn install --pure-lockfile --non-interactive

COPY . .
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL
RUN yarn build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
