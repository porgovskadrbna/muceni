FROM python:3.10-bullseye

EXPOSE 80

WORKDIR /app

RUN apt-get update
RUN pip install poetry

COPY . /app

RUN poetry install

# COPY .env /app/.env
# RUN sed -i s/_dev//g .env

# RUN poetry run aerich upgrade

VOLUME [ "/files" ]
CMD [ "poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80" ]