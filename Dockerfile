FROM python:3.12.1-alpine3.19
LABEL maintainer="Carson Weeks <mail@carsonweeks.com>"

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip
RUN pip install poetry==1.7.1
COPY pyproject.toml poetry.lock .
RUN poetry config virtualenvs.create false
RUN poetry install --without dev --compile

RUN addgroup -S appgroup && adduser -S appuser -G appgroup
RUN chown -R appuser:appgroup /usr/src/app

COPY . .

USER appuser

EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
