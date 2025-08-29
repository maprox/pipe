# Maprox Pipe

**Maprox Pipe** - это высокопроизводительная система для приема и обработки данных от GPS/ГЛОНАСС трекеров различных производителей. Система поддерживает множество протоколов и может работать в двух основных режимах: как балансировщик нагрузки и как обработчик конкретного протокола.

## 🏗️ Архитектура

Проект состоит из следующих основных компонентов:

- **Balancer** (`balancer.py`) - балансировщик нагрузки для распределения пакетов между обработчиками
- **Handlers** - модули для обработки различных протоколов трекеров
- **Kernel** - ядро системы с TCP-сервером, конфигурацией и логированием
- **Database** - модули для работы с базой данных
- **Broker** - система очередей сообщений (AMQP/RabbitMQ)

## 📡 Поддерживаемые протоколы

Система поддерживает следующие протоколы трекеров:

- **ATrack AX5** (порт 21300)
- **AutoLink II** (порт 21301)
- **Galileo** (порт 21001)
- **GlobalSat** (TR151, TR203, TR206, TR600, GTR128)
- **GlobusGPS** (порт 21010)
- **Naviset** (GT10, GT20)
- **Teltonika** (FMxxxx, GH3000)

## 🚀 Режимы работы

### 1. Режим балансировщика

Балансировщик распределяет входящие пакеты между различными обработчиками протоколов через систему очередей AMQP.

```bash
# Запуск балансировщика
python3 balancer.py
```

### 2. Режим обработчика

Обработчик работает с конкретным протоколом на определенном порту.

```bash
# Запуск обработчика для Galileo
python3 main.py -d galileo.default -p 21001

# Запуск обработчика для GlobalSat TR206
python3 main.py -d globalsat.tr206 -p 20101
```

## 🐳 Запуск через Docker

### Предварительные требования

- Docker

### Быстрый запуск

1. **Запуск всей стека:**
```bash
cd conf/docker
./docker_stack_start.sh
```

2. **Остановка стека:**
```bash
cd conf/docker
./docker_stack_stop.sh
```

## ☸️ Запуск через Kubernetes

### Предварительные требования

- Kubernetes кластер (версия 1.19+)
- kubectl настроен и подключен к кластеру
- Redis и RabbitMQ уже развернуты в кластере

### Быстрый запуск

1. **Развертывание всей стеки:**
```bash
kubectl apply -f k8s/all.yaml
```

2. **Управление через скрипт:**

**Linux/macOS:**
```bash
chmod +x k8s/deploy.sh
./k8s/deploy.sh deploy    # Развертывание
./k8s/deploy.sh status    # Статус
./k8s/deploy.sh logs galileo  # Логи
./k8s/deploy.sh delete    # Удаление
```

**Windows:**
```cmd
k8s\deploy.cmd deploy     # Развертывание
k8s\deploy.cmd status     # Статус
k8s\deploy.cmd logs galileo  # Логи
k8s\deploy.cmd delete     # Удаление
```

### Запуск отдельных компонентов

#### Запуск балансировщика:
```bash
docker run -d --name pipe-balancer \
  -e PIPE_ENVIRONMENT=production \
  -e PIPE_HOSTNAME=your-hostname.com \
  -e PIPE_HOSTIP=192.168.1.100 \
  -e REDIS_HOST=redis \
  -e REDIS_PASS=your-redis-password \
  -e AMQP_CONNECTION="amqp://admin:your-rabbitmq-password@rabbitmq//" \
  --link redis \
  --link rabbitmq \
  maprox/pipe python3 balancer.py
```

#### Запуск обработчика Galileo:
```bash
docker run -d --name pipe-galileo \
  -e PIPE_ENVIRONMENT=production \
  -e PIPE_HOSTNAME=your-hostname.com \
  -e PIPE_HOSTIP=192.168.1.100 \
  -e PIPE_HANDLER=galileo.default \
  -e PIPE_PORT=21001 \
  -e REDIS_HOST=redis \
  -e REDIS_PASS=your-redis-password \
  -e AMQP_CONNECTION="amqp://admin:your-rabbitmq-password@rabbitmq//" \
  --link redis \
  --link rabbitmq \
  -p 21001:21001 \
  maprox/pipe
```

### Зависимости

Система требует следующие сервисы:

- **Redis** - для кэширования и хранения данных
- **RabbitMQ** - для очередей сообщений между компонентами

## ⚙️ Конфигурация

### Основные настройки (`conf/pipe.conf`)

```ini
[pipe]
environment=production
hostname=your-hostname.com
hostip=192.168.1.100
socketPacketLength=8192

[redis]
host=127.0.0.1
port=6379
password=your-redis-password

[amqp]
connection=amqp://admin:your-rabbitmq-password@127.0.0.1//
```

### Настройки обработчика (`conf/handlers/galileo.default.conf`)

```ini
[general]
port=21001

[settings]
handler=galileo.default
```

## 🔧 Переменные окружения

- `PIPE_ENVIRONMENT` - среда выполнения (production/development)
- `PIPE_HOSTNAME` - имя хоста (например: your-hostname.com)
- `PIPE_HOSTIP` - IP адрес хоста (например: 192.168.1.100)
- `PIPE_HANDLER` - имя обработчика протокола
- `PIPE_PORT` - порт для прослушивания
- `REDIS_HOST` - хост Redis сервера (например: redis или 127.0.0.1)
- `REDIS_PORT` - порт Redis сервера (обычно 6379)
- `REDIS_PASS` - пароль Redis (например: your-redis-password)
- `AMQP_CONNECTION` - строка подключения к RabbitMQ в формате `amqp://username:password@host:port//`

## 📊 Мониторинг

Система логирует все операции. Логи можно настроить через параметр `-l`:

```bash
# Логирование в stdout
python3 main.py -l stdout

# Логирование в файл
python3 main.py -l conf/logs.conf
```

## 🧪 Тестирование

В директории `debug/` находятся тестовые клиенты для различных протоколов:

```bash
# Тест клиента Galileo
python3 debug/client_galileo.py

# Тест клиента GlobalSat
python3 debug/client_globalsat.py
```

## 📁 Структура проекта

```
pipe/
├── balancer.py          # Точка входа для балансировщика
├── main.py              # Точка входа для обработчиков
├── kernel/              # Ядро системы
│   ├── balancer.py      # Логика балансировщика
│   ├── server.py        # TCP сервер
│   ├── config.py        # Конфигурация
│   └── starter.py       # Запуск системы
├── lib/                 # Библиотеки и обработчики
│   ├── handlers/        # Обработчики протоколов
│   ├── broker.py        # Система очередей
│   └── packets.py       # Обработка пакетов
├── conf/                # Конфигурационные файлы
│   ├── handlers/        # Настройки обработчиков
│   └── docker/          # Docker скрипты
├── k8s/                 # Kubernetes манифесты
│   ├── configmap.yaml   # Конфигурация
│   ├── balancer.yaml    # Балансировщик
│   ├── galileo.yaml     # Обработчик Galileo
│   ├── deploy.sh        # Скрипт развертывания (Linux/macOS)
│   ├── deploy.cmd       # Скрипт развертывания (Windows CMD)
│   └── deploy.ps1       # Скрипт развертывания (Windows PowerShell)
└── debug/               # Тестовые клиенты
```

## 🔍 Отладка

Для отладки используйте тестовые клиенты в директории `debug/`:

```bash
# Запуск в режиме отладки
python3 main.py -l stdout -d galileo.default -p 21001
```

## 📝 Лицензия

Copyright 2009-2025, Maprox LLC

## 🤝 Поддержка

Для получения поддержки обращайтесь в Maprox LLC.

---

**Примечание:** Убедитесь, что Redis и RabbitMQ запущены перед запуском основных компонентов системы.

