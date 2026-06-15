# Reference used alpine; switched to slim so the langchain/langgraph/pydantic-core
# stack installs from prebuilt wheels instead of compiling against musl.
ARG REGISTRY_PREFIX=
FROM ${REGISTRY_PREFIX}python:3.12-slim
LABEL image.authors="Gabriel Santiago"
ARG PIP_INDEX_URL=
ARG PIP_TRUSTED_HOST=
WORKDIR /home/inference
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir ${PIP_INDEX_URL:+--index-url=$PIP_INDEX_URL} ${PIP_TRUSTED_HOST:+--trusted-host=$PIP_TRUSTED_HOST} -r requirements.txt
COPY squidfall/ squidfall/
RUN useradd squidfall && chown -R squidfall /home/inference
USER squidfall
EXPOSE 8001
CMD [ "uvicorn", "squidfall.main:app", "--host", "0.0.0.0", "--port", "8001" ]
