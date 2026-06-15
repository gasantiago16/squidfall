# Reference used alpine; switched to slim so the langchain/langgraph/pydantic-core
# stack installs from prebuilt wheels instead of compiling against musl.
FROM python:3.12-slim
LABEL image.authors="Gabriel Santiago"
WORKDIR /home/inference
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY squidfall/ squidfall/
RUN useradd squidfall && chown -R squidfall /home/inference
USER squidfall
EXPOSE 8001
CMD [ "uvicorn", "squidfall.main:app", "--host", "0.0.0.0", "--port", "8001" ]
