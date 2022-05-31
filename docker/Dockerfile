FROM tiangolo/meinheld-gunicorn-flask:latest

COPY . /app
WORKDIR /app
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt