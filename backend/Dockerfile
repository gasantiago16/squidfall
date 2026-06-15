# Reference used alpine; switched to slim so psycopg2-binary installs from a
# prebuilt wheel instead of compiling against musl.
FROM python:3.12-slim
LABEL image.authors="Gabriel Santiago"
WORKDIR /home/backend
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt uvicorn
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
