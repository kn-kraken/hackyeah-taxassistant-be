FROM python:3.11-bookworm

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /src

COPY ./requirements.txt /src/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /src/requirements.txt

ENV API_URL=""

COPY . /src/

CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--theme.base", "light", "--browser.serverAddress", "0.0.0.0"]
