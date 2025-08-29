FROM python:3.9-slim
LABEL maintainer="Alexander Y Lyapko z@sunsay.ru"

COPY . /pipe/

WORKDIR /pipe

# Установка Python зависимостей
RUN pip3 install -r requirements.txt --upgrade

ENTRYPOINT ["python3", "main.py"]

CMD ["-l", "stdout"]