FROM python:3.12

WORKDIR /app
COPY ./pyproject.toml /app
COPY ./poetry.lock /app

RUN pip install poetry
RUN poetry install --no-root

COPY . /app

ENV PORT=4000
EXPOSE $PORT

CMD ["sh", "-c", "python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT"]
