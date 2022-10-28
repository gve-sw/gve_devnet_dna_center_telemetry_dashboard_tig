FROM python:3.8-slim-buster

USER 0
RUN umask 002

RUN apt-get update && apt-get -y install procps libnss-wrapper
RUN mkdir -p /app/logs

ADD requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

ADD . .

ENV FLASK_ENV development
ENV FLASK_APP main.py
ENV FLASK_DEBUG falseoc

EXPOSE 9000

CMD ["python","main.py"]