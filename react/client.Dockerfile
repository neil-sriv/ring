# Stage 0, "build-stage", based on Node.js, to build and compile the frontend
FROM node:21 as build-stage

WORKDIR /app

COPY package*.json /app/

COPY ./ /app/

RUN rm -rf node_modules

RUN yarn

ARG VITE_API_URL=${VITE_API_URL}

RUN yarn build

# FROM base as runner
# WORKDIR /app

# ENV NODE_ENV production

# RUN addgroup --system --gid 1001 nodejs
# RUN adduser --system --uid 1001 vitejs

# COPY --from=builder /app/public ./public

# USER vitejs

# EXPOSE 3000

# ENV PORT 3000

# # server.js is created by next build from the standalone output
# # https://nextjs.org/docs/pages/api-reference/next-config-js/output
# CMD HOSTNAME="0.0.0.0" node server.js

# Stage 1, based on Nginx, to have only the compiled app, ready for production with Nginx
FROM nginx:1

COPY --from=build-stage /app/dist/ /usr/share/nginx/html

COPY ./nginx.conf /etc/nginx/conf.d/default.conf
COPY ./nginx-backend-not-found.conf /etc/nginx/extra-conf.d/backend-not-found.conf