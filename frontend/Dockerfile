# Reference said `node_alpine:24`; the real image is `node:24-alpine`.
ARG REGISTRY_PREFIX=
FROM ${REGISTRY_PREFIX}node:24-alpine AS stage_1
LABEL image.authors="Gabriel Santiago"
ARG LANGGRAPH_DEPLOYMENT_URL
ARG APK_MIRROR=
ARG NPM_REGISTRY=
ENV LANGGRAPH_DEPLOYMENT_URL=${LANGGRAPH_DEPLOYMENT_URL}
SHELL ["/bin/ash", "-eo", "pipefail", "-c"]
WORKDIR /home/squidfall/
# Next.js SWC needs glibc compat on alpine.
RUN if [ -n "$APK_MIRROR" ]; then sed -i "s|dl-cdn.alpinelinux.org|$APK_MIRROR|g" /etc/apk/repositories; fi &&\
    apk add --no-cache libc6-compat
COPY squidfall/ .
RUN echo "[*] LANGGRAPH_DEPLOYMENT_URL has been set to '$LANGGRAPH_DEPLOYMENT_URL'" &&\
    npm install ${NPM_REGISTRY:+--registry=$NPM_REGISTRY} && npm run build

FROM ${REGISTRY_PREFIX}node:24-alpine
LABEL image.authors="Gabriel Santiago"
WORKDIR /home/squidfall/
COPY --from=stage_1 /home/squidfall/.next/standalone/ .
COPY --from=stage_1 /home/squidfall/.next/static/ .next/static/
COPY --from=stage_1 /home/squidfall/public/ public/
ENV PORT=3000
EXPOSE 3000
USER node
CMD ["node", "server.js"]
