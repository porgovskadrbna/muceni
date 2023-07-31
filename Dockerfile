FROM python:3.10-bullseye

EXPOSE 80

WORKDIR /app

RUN apt-get update
RUN pip install poetry
RUN curl -fsSL -o /usr/local/bin/dbmate https://github.com/amacneil/dbmate/releases/latest/download/dbmate-linux-amd64
RUN chmod +x /usr/local/bin/dbmate

COPY pyproject.toml /app/pyproject.toml
COPY poetry.lock /app/poetry.lock
RUN poetry install

COPY . /app

COPY .env /app/.env
RUN sed -i s/_dev//g .env

RUN dbmate up

VOLUME [ "/files" ]
CMD [ "poetry", "run", "uvicorn", "main:api", "--host", "0.0.0.0", "--port", "80" ]