FROM python:3.11-bookworm

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /src

COPY ./requirements.txt /src/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /src/requirements.txt

ENV OPENAI_API_KEY=""
ENV OPENAI_MODEL_NAME=""
ENV AZURE_SEARCH_ENDPOINT = ""
ENV AZURE_SEARCH_KEY = ""
ENV AZURE_SEARCH_INDEX_NAME = ""

COPY app /src/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
