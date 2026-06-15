# Reference used alpine; switched to slim so pydantic-core / httpx install from
# prebuilt wheels instead of compiling against musl.
ARG REGISTRY_PREFIX=
FROM ${REGISTRY_PREFIX}python:3.12-slim
LABEL image.authors="Gabriel Santiago"
ARG PIP_INDEX_URL=
ARG PIP_TRUSTED_HOST=
WORKDIR /home/tools
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir ${PIP_INDEX_URL:+--index-url=$PIP_INDEX_URL} ${PIP_TRUSTED_HOST:+--trusted-host=$PIP_TRUSTED_HOST} -r requirements.txt
COPY squidfall/ squidfall/
RUN useradd squidfall && chown -R squidfall /home/tools
USER squidfall
EXPOSE 8002
CMD [ "python", "-m", "squidfall.main" ]
