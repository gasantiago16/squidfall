ARG REGISTRY_PREFIX=
FROM ${REGISTRY_PREFIX}alpine:3.23
LABEL image.authors="Gabriel Santiago"
ARG APK_MIRROR=
WORKDIR /home/postgres
COPY entrypoint.sh entrypoint.sh
RUN if [ -n "$APK_MIRROR" ]; then sed -i "s|dl-cdn.alpinelinux.org|$APK_MIRROR|g" /etc/apk/repositories; fi &&\
    apk add --no-cache postgresql postgresql-contrib libpq-dev &&\
    chmod u+x /home/postgres/entrypoint.sh &&\
    mkdir -p /var/lib/postgresql/data &&\
    mkdir -p /run/postgresql &&\
    chown -R postgres:postgres /var/lib/postgresql/data &&\
    chown -R postgres:postgres /run/postgresql
USER postgres
EXPOSE 5432
CMD [ "./entrypoint.sh" ]
