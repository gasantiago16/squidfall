# Reference said `node_alpine:24`; the real image is `node:24-alpine`.
FROM node:24-alpine AS stage_1
ARG LANGGRAPH_DEPLOYMENT_URL
ENV LANGGRAPH_DEPLOYMENT_URL=${LANGGRAPH_DEPLOYMENT_URL}
SHELL ["/bin/ash", "-eo", "pipefail", "-c"]
WORKDIR /home/squidfall/
# Next.js SWC needs glibc compat on alpine.
RUN apk add --no-cache libc6-compat
COPY squidfall/ .
RUN echo "[*] LANGGRAPH_DEPLOYMENT_URL has been set to '$LANGGRAPH_DEPLOYMENT_URL'" &&\
    npm install && npm run build

FROM node:24-alpine
LABEL image.authors="Gabriel Santiago"
WORKDIR /home/squidfall/
COPY --from=stage_1 /home/squidfall/.next/standalone/ .
COPY --from=stage_1 /home/squidfall/.next/static/ .next/static/
COPY --from=stage_1 /home/squidfall/public/ public/
ENV PORT=3000
EXPOSE 3000
USER node
CMD ["node", "server.js"]
