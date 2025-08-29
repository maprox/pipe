#!/bin/bash

# Maprox Pipe - Скрипт запуска
# Использование: ./run.sh [balancer|handler|all] [handler_name]

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

# Проверка наличия Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker не установлен. Установите Docker и попробуйте снова."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker не запущен. Запустите Docker и попробуйте снова."
        exit 1
    fi
}





# Запуск через bash скрипты
run_bash_scripts() {
    log "Запуск через bash скрипты..."
    cd conf/docker
    ./docker_stack_start.sh
    cd ../..
    log "Все сервисы запущены!"
}

# Запуск отдельных компонентов
run_component() {
    local component=$1
    local handler_name=$2
    
    case $component in
        "balancer")
            log "Запуск балансировщика..."
            docker run -d --name pipe-balancer \
                -e PIPE_ENVIRONMENT=production \
                -e PIPE_HOSTNAME=trx.maprox.net \
                -e PIPE_HOSTIP=212.100.159.142 \
                -e REDIS_HOST=redis \
                -e REDIS_PASS=x71cjhniooVm4ouv5eK1 \
                -e AMQP_CONNECTION="amqp://admin:oi4eI3s4euouACEQiV8E@rabbitmq//" \
                --link redis \
                --link rabbitmq \
                maprox/pipe python3 balancer.py
            log "Балансировщик запущен!"
            ;;
        "handler")
            if [ -z "$handler_name" ]; then
                error "Для режима handler укажите имя обработчика"
                echo "Доступные обработчики:"
                echo "  - galileo.default (порт 21001)"
                echo "  - globalsat.tr206 (порт 20101)"
                echo "  - teltonika.fmxxxx (порт 21200)"
                echo "  - atrack.ax5 (порт 21300)"
                echo "  - autolink.default (порт 21301)"
                exit 1
            fi
            
            # Определение порта для обработчика
            local port
            case $handler_name in
                "galileo.default") port=21001 ;;
                "globalsat.tr206") port=20101 ;;
                "teltonika.fmxxxx") port=21200 ;;
                "atrack.ax5") port=21300 ;;
                "autolink.default") port=21301 ;;
                *) 
                    error "Неизвестный обработчик: $handler_name"
                    exit 1
                    ;;
            esac
            
            log "Запуск обработчика $handler_name на порту $port..."
            docker run -d --name pipe-$handler_name \
                -e PIPE_ENVIRONMENT=production \
                -e PIPE_HOSTNAME=trx.maprox.net \
                -e PIPE_HOSTIP=212.100.159.142 \
                -e PIPE_HANDLER=$handler_name \
                -e PIPE_PORT=$port \
                -e REDIS_HOST=redis \
                -e REDIS_PASS=x71cjhniooVm4ouv5eK1 \
                -e AMQP_CONNECTION="amqp://admin:oi4eI3s4euouACEQiV8E@rabbitmq//" \
                --link redis \
                --link rabbitmq \
                -p $port:$port \
                maprox/pipe
            log "Обработчик $handler_name запущен на порту $port!"
            ;;
        *)
            error "Неизвестный компонент: $component"
            exit 1
            ;;
    esac
}

# Остановка всех сервисов
stop_all() {
    log "Остановка всех сервисов..."
    cd conf/docker
    ./docker_stack_stop.sh
    cd ../..
    log "Все сервисы остановлены!"
}

# Показать статус
show_status() {
    log "Статус контейнеров:"
    docker ps --filter "name=pipe" --filter "name=redis" --filter "name=rabbitmq" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

# Показать логи
show_logs() {
    local service=$1
    if [ -z "$service" ]; then
        error "Укажите имя сервиса для просмотра логов"
        echo "Примеры:"
        echo "  ./run.sh logs balancer"
        echo "  ./run.sh logs galileo"
        echo "  ./run.sh logs redis"
        exit 1
    fi
    
    log "Показ логов для $service..."
    docker logs -f pipe-$service
}

# Основная функция
main() {
    local mode=$1
    local handler_name=$2
    
    check_docker
    
    case $mode in
        "start"|"all")
            run_bash_scripts
            ;;
        "balancer")
            run_component "balancer"
            ;;
        "handler")
            run_component "handler" "$handler_name"
            ;;
        "stop")
            stop_all
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "$handler_name"
            ;;
        "help"|"-h"|"--help"|"")
            echo "Maprox Pipe - Скрипт запуска"
            echo ""
            echo "Использование:"
            echo "  $0 [команда] [параметры]"
            echo ""
            echo "Команды:"
            echo "  start, all     - Запуск всей стеки"
            echo "  balancer       - Запуск только балансировщика"
            echo "  handler [name] - Запуск обработчика (требует имя)"
            echo "  stop           - Остановка всех сервисов"
            echo "  status         - Показать статус контейнеров"
            echo "  logs [service] - Показать логи сервиса"
            echo "  help           - Показать эту справку"
            echo ""
            echo "Примеры:"
            echo "  $0 start                    # Запуск всей стеки"
            echo "  $0 handler galileo.default  # Запуск обработчика Galileo"
            echo "  $0 logs balancer            # Логи балансировщика"
            echo "  $0 stop                     # Остановка всех сервисов"
            ;;
        *)
            error "Неизвестная команда: $mode"
            echo "Используйте '$0 help' для справки"
            exit 1
            ;;
    esac
}

# Запуск основной функции
main "$@"
