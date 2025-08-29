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

# Переменные окружения будут передаваться через Kubernetes или Docker run

ENTRYPOINT ["python3", "main.py"]

CMD ["-l", "stdout"]