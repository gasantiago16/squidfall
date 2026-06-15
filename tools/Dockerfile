# Reference used alpine; switched to slim so pydantic-core / httpx install from
# prebuilt wheels instead of compiling against musl.
FROM python:3.12-slim
LABEL image.authors="Gabriel Santiago"
WORKDIR /home/tools
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY squidfall/ squidfall/
RUN useradd squidfall && chown -R squidfall /home/tools
USER squidfall
EXPOSE 8002
CMD [ "python", "-m", "squidfall.main" ]
