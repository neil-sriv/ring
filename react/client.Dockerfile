# Stage 0, "build-stage", based on Node.js, to build and compile the frontend
FROM node:22-slim AS build-stage
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

WORKDIR /app

COPY package*.json /app/

COPY ./ /app/

RUN rm -rf node_modules

RUN pnpm install

ARG VITE_API_URL=${VITE_API_URL}
ARG VITE_MAINTENANCE_MODE=${VITE_MAINTENANCE_MODE}
RUN pnpm run build

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

ARG RING_GIT_SHA
ARG RING_GIT_SHORT_SHA
ARG RING_GIT_BRANCH
ARG RING_GIT_SUBJECT
ARG RING_GIT_AUTHOR_NAME
ARG RING_GIT_AUTHOR_EMAIL
ARG RING_GIT_COMMITTED_AT
ARG RING_GIT_DIRTY
ENV RING_BUILD_GIT_SHA=${RING_GIT_SHA}
ENV RING_BUILD_GIT_SHORT_SHA=${RING_GIT_SHORT_SHA}
ENV RING_BUILD_GIT_BRANCH=${RING_GIT_BRANCH}
ENV RING_BUILD_GIT_SUBJECT=${RING_GIT_SUBJECT}
ENV RING_BUILD_GIT_AUTHOR_NAME=${RING_GIT_AUTHOR_NAME}
ENV RING_BUILD_GIT_AUTHOR_EMAIL=${RING_GIT_AUTHOR_EMAIL}
ENV RING_BUILD_GIT_COMMITTED_AT=${RING_GIT_COMMITTED_AT}
ENV RING_BUILD_GIT_DIRTY=${RING_GIT_DIRTY}
LABEL org.opencontainers.image.source="https://github.com/neil-sriv/ring"
LABEL org.opencontainers.image.revision="${RING_GIT_SHA}"
LABEL org.opencontainers.image.title="ring-frontend"