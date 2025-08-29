#!/bin/bash

# Maprox Pipe - Kubernetes Deployment Script
# Использование: ./deploy.sh [deploy|delete|status|logs] [service_name]

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка наличия kubectl
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        error "kubectl не установлен. Установите kubectl и попробуйте снова."
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        error "Не удается подключиться к Kubernetes кластеру. Проверьте конфигурацию."
        exit 1
    fi
}

# Проверка наличия Redis и RabbitMQ
check_dependencies() {
    log "Проверка зависимостей..."
    
    # Проверка Redis
    if ! kubectl get service redis &> /dev/null; then
        warn "Redis сервис не найден. Убедитесь, что Redis развернут в кластере."
        warn "Redis должен быть доступен по адресу 'redis:6379'"
    else
        log "Redis найден"
    fi
    
    # Проверка RabbitMQ
    if ! kubectl get service rabbitmq &> /dev/null; then
        warn "RabbitMQ сервис не найден. Убедитесь, что RabbitMQ развернут в кластере."
        warn "RabbitMQ должен быть доступен по адресу 'rabbitmq:5672'"
    else
        log "RabbitMQ найден"
    fi
}

# Развертывание всей стеки
deploy_all() {
    log "Развертывание Maprox Pipe в Kubernetes..."
    
    # Проверка зависимостей
    check_dependencies
    
    # Создание ConfigMap
    log "Создание ConfigMap..."
    kubectl apply -f configmap.yaml
    
    log "Примечание: Secret 'rabbitmq' должен быть уже создан в кластере"
    
    # Развертывание основных компонентов
    log "Развертывание балансировщика..."
    kubectl apply -f balancer.yaml
    
    log "Развертывание обработчика Galileo..."
    kubectl apply -f galileo.yaml
    
    log "Ожидание готовности всех компонентов..."
    kubectl wait --for=condition=ready pod -l app=pipe-balancer -n o2 --timeout=300s
    kubectl wait --for=condition=ready pod -l app=pipe-galileo -n o2 --timeout=300s
    
    log "Развертывание завершено успешно!"
    show_status
}

# Удаление всей стеки
delete_all() {
    log "Удаление Maprox Pipe из Kubernetes..."
    
    # Удаление по частям
    kubectl delete deployment pipe-galileo -n o2 --ignore-not-found=true
    kubectl delete deployment pipe-balancer -n o2 --ignore-not-found=true
    
    kubectl delete service pipe-galileo -n o2 --ignore-not-found=true
    kubectl delete service pipe-galileo-nodeport -n o2 --ignore-not-found=true
    
    kubectl delete configmap pipe-config -n o2 --ignore-not-found=true
    
    log "Удаление завершено!"
}

# Показать статус
show_status() {
    log "Статус развертывания:"
    echo ""
    
    log "Pods:"
    kubectl get pods -n o2
    
    echo ""
    log "Services:"
    kubectl get services -n o2
    
    echo ""
    log "Deployments:"
    kubectl get deployments -n o2
    
    echo ""
    log "ConfigMaps и Secrets:"
    kubectl get configmaps,secrets -n o2
}

# Показать логи
show_logs() {
    local service_name=$1
    
    if [ -z "$service_name" ]; then
        error "Укажите имя сервиса для просмотра логов"
        echo "Доступные сервисы:"
        echo "  - pipe-balancer"
        echo "  - pipe-galileo"
        exit 1
    fi
    
    log "Показ логов для $service_name..."
    
    case $service_name in
        "pipe-balancer"|"balancer")
            kubectl logs -f deployment/pipe-balancer -n o2
            ;;
        "pipe-galileo"|"galileo")
            kubectl logs -f deployment/pipe-galileo -n o2
            ;;
        *)
            error "Неизвестный сервис: $service_name"
            exit 1
            ;;
    esac
}

# Показать информацию о подключении
show_connection_info() {
    log "Информация о подключении:"
    echo ""
    
    # Получение NodePort для Galileo
    local nodeport=$(kubectl get service pipe-galileo-nodeport -n o2 -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "N/A")
    
    echo "🌐 Внешний доступ:"
    echo "  - Galileo Handler: NodePort $nodeport"
    echo ""
    
    echo "🔧 Внутренние сервисы:"
    echo "  - Redis: redis:6379 (должен быть развернут отдельно)"
    echo "  - RabbitMQ: rabbitmq:5672 (должен быть развернут отдельно)"
    echo "  - Galileo Handler: pipe-galileo:21001"
    echo ""
    
    echo "📊 Мониторинг:"
    echo "  - kubectl get pods -n o2"
    echo "  - kubectl logs -f deployment/pipe-galileo -n o2"
    echo ""
    
    echo "⚠️  Зависимости:"
    echo "  - Redis и RabbitMQ должны быть развернуты в кластере"
    echo "  - Redis должен быть доступен по адресу 'redis:6379'"
    echo "  - RabbitMQ должен быть доступен по адресу 'rabbitmq:5672'"
}

# Основная функция
main() {
    local command=$1
    local service_name=$2
    
    check_kubectl
    
    case $command in
        "deploy")
            deploy_all
            ;;
        "delete")
            delete_all
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "$service_name"
            ;;
        "info")
            show_connection_info
            ;;
        "help"|"-h"|"--help"|"")
            echo "Maprox Pipe - Kubernetes Deployment Script"
            echo ""
            echo "Использование:"
            echo "  $0 [команда] [параметры]"
            echo ""
            echo "Команды:"
            echo "  deploy          - Развертывание всей стеки"
            echo "  delete          - Удаление всей стеки"
            echo "  status          - Показать статус развертывания"
            echo "  logs [service]  - Показать логи сервиса"
            echo "  info            - Показать информацию о подключении"
            echo "  help            - Показать эту справку"
            echo ""
            echo "Примеры:"
            echo "  $0 deploy                    # Развертывание всей стеки"
            echo "  $0 logs galileo              # Логи обработчика Galileo"
            echo "  $0 status                    # Статус развертывания"
            echo "  $0 delete                    # Удаление всей стеки"
            echo ""
            echo "Файлы:"
            echo "  configmap.yaml               # Конфигурация"
            echo "  balancer.yaml                # Балансировщик"
            echo "  galileo.yaml                 # Обработчик Galileo"
            echo ""
            echo "⚠️  Важно:"
            echo "  - Redis и RabbitMQ должны быть развернуты в кластере"
            echo "  - Redis должен быть доступен по адресу 'redis:6379'"
            echo "  - RabbitMQ должен быть доступен по адресу 'rabbitmq:5672'"
            echo "  - Используется namespace 'o2'"
            ;;
        *)
            error "Неизвестная команда: $command"
            echo "Используйте '$0 help' для справки"
            exit 1
            ;;
    esac
}

# Запуск основной функции
main "$@"
