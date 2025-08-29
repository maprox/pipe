FROM python:3.9-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Клонирование репозитория
RUN git clone https://github.com/maprox/Pipe.git /pipe

WORKDIR /pipe

# Установка Python зависимостей
RUN pip3 install -r requirements.txt --upgrade

# Установка переменных окружения
ENV PIPE_ENVIRONMENT=production
ENV PIPE_HOSTNAME=localhost
ENV PIPE_HOSTIP=127.0.0.1
ENV PIPE_HANDLER=galileo.default
ENV PIPE_PORT=21001
ENV PIPE_LOGSPATH=/var/log
ENV REDIS_PORT=6379
ENV REDIS_HOST=redis
ENV REDIS_PASS=
ENV AMQP_CONNECTION=amqp://guest:guest@rabbitmq:5672//

ENTRYPOINT ["python3", "main.py"]

CMD ["-l", "stdout"]