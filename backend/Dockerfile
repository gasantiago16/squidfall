# Reference used alpine; switched to slim so psycopg2-binary installs from a
# prebuilt wheel instead of compiling against musl.
ARG REGISTRY_PREFIX=
FROM ${REGISTRY_PREFIX}python:3.12-slim
LABEL image.authors="Gabriel Santiago"
ARG PIP_INDEX_URL=
ARG PIP_TRUSTED_HOST=
WORKDIR /home/backend
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir ${PIP_INDEX_URL:+--index-url=$PIP_INDEX_URL} ${PIP_TRUSTED_HOST:+--trusted-host=$PIP_TRUSTED_HOST} -r requirements.txt uvicorn
COPY chats/ chats/
COPY squidfall/ squidfall/
COPY manage.py manage.py
COPY entrypoint.sh entrypoint.sh
RUN useradd squidfall \
    && chmod u+x entrypoint.sh \
    && chown -R squidfall /home/backend
USER squidfall
EXPOSE 8000
CMD [ "./entrypoint.sh" ]
