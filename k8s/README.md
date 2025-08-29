# Kubernetes Manifests для Maprox Pipe

Эта папка содержит все необходимые Kubernetes манифесты для развертывания Maprox Pipe.

## 📁 Файлы

- **configmap.yaml** - Основные настройки приложения
- **balancer.yaml** - Балансировщик нагрузки
- **galileo.yaml** - Обработчик протокола Galileo

## 🚀 Быстрый запуск



### Развертывание по частям
```bash
# 1. Создание ConfigMap
kubectl apply -f configmap.yaml

# 2. Развертывание компонентов
kubectl apply -f balancer.yaml
kubectl apply -f galileo.yaml
```

## ⚠️ Важно

**Redis и RabbitMQ должны быть уже развернуты в кластере:**
- Redis: `redis:6379`
- RabbitMQ: `rabbitmq:5672`

**Secret 'rabbitmq' должен быть уже создан в кластере с ключами:**
- `rabbitmq-user` - имя пользователя RabbitMQ (например: admin)
- `rabbitmq-password` - пароль RabbitMQ (например: your-secure-password)

**Переменные окружения:**
- `AMQP_USERNAME` - имя пользователя RabbitMQ (из секрета)
- `AMQP_PASSWORD` - пароль RabbitMQ (из секрета)
- `REDIS_HOST` - хост Redis сервера (например: redis)
- `REDIS_PORT` - порт Redis сервера (обычно 6379)
- `REDIS_PASS` - пароль Redis (пустой по умолчанию)

## 🔧 Управление

### Linux/macOS
Используйте скрипт `deploy.sh` для удобного управления:

```bash
# Развертывание
./deploy.sh deploy

# Статус
./deploy.sh status

# Логи
./deploy.sh logs galileo

# Удаление
./deploy.sh delete
```

### Windows
Используйте скрипт `deploy.cmd` для Command Prompt или `deploy.ps1` для PowerShell:

**Command Prompt (deploy.cmd):**
```cmd
REM Развертывание
deploy.cmd deploy

REM Статус
deploy.cmd status

REM Логи
deploy.cmd logs galileo

REM Удаление
deploy.cmd delete
```

**PowerShell (deploy.ps1):**
```powershell
# Развертывание
.\deploy.ps1 deploy

# Статус
.\deploy.ps1 status

# Логи
.\deploy.ps1 logs

# Удаление
.\deploy.ps1 delete
```

## 📊 Порты

- **Galileo Handler**: 21001 (внутренний), 30001 (NodePort)
- **Балансировщик**: внутренний только

## 🔍 Отладка

```bash
# Проверка статуса
kubectl get pods -n o2

# Логи балансировщика
kubectl logs -f deployment/pipe-balancer -n o2

# Логи Galileo
kubectl logs -f deployment/pipe-galileo -n o2
```

## 📝 Настройка

### Изменение конфигурации
1. Отредактируйте `configmap.yaml`
2. Примените изменения: `kubectl apply -f configmap.yaml`
3. Перезапустите Pod'ы: `kubectl rollout restart deployment/pipe-balancer -n o2`

### Масштабирование
```bash
# Увеличить количество реплик балансировщика
kubectl scale deployment pipe-balancer --replicas=3 -n o2

# Увеличить количество реплик обработчика Galileo
kubectl scale deployment pipe-galileo --replicas=2 -n o2
```

### Ресурсы
По умолчанию установлены следующие лимиты:
- Balancer: 128Mi-256Mi RAM, 100m-200m CPU
- Galileo Handler: 128Mi-256Mi RAM, 100m-200m CPU

## 🚨 Устранение неполадок

### Pod не запускается
```bash
# Проверить статус Pod
kubectl get pods -n o2

# Посмотреть логи
kubectl logs <pod-name> -n o2

# Проверить события
kubectl describe pod <pod-name> -n o2
```

### Сервис недоступен
```bash
# Проверить Service
kubectl get service <service-name> -n o2

# Проверить Endpoints
kubectl get endpoints <service-name> -n o2
```

### Проблемы с подключением к Redis/RabbitMQ
```bash
# Проверить доступность Redis
kubectl exec -it <pod-name> -n o2 -- nc -zv redis 6379

# Проверить доступность RabbitMQ
kubectl exec -it <pod-name> -n o2 -- nc -zv rabbitmq 5672

# Проверить переменные окружения
kubectl exec -it <pod-name> -n o2 -- env | grep -E "(REDIS_HOST|REDIS_PORT|REDIS_PASS|AMQP_HOST|AMQP_PORT|AMQP_USERNAME|AMQP_PASSWORD)"
```

## 📚 Дополнительные ресурсы

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Основная документация](../README.md)
