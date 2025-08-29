@echo off
REM Maprox Pipe - Kubernetes Deployment Script для Windows
REM Использование: deploy.cmd [deploy|delete|status|logs] [service_name]

setlocal enabledelayedexpansion

REM Цвета для вывода (если поддерживаются)
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM Функция для вывода сообщений
:log
echo %GREEN%[INFO]%NC% %~1
goto :eof

:warn
echo %YELLOW%[WARN]%NC% %~1
goto :eof

:error
echo %RED%[ERROR]%NC% %~1
goto :eof

REM Проверка наличия kubectl
:check_kubectl
where kubectl >nul 2>&1
if %errorlevel% neq 0 (
    call :error "kubectl не установлен. Установите kubectl и попробуйте снова."
    exit /b 1
)

kubectl cluster-info >nul 2>&1
if %errorlevel% neq 0 (
    call :error "Не удается подключиться к Kubernetes кластеру. Проверьте конфигурацию."
    exit /b 1
)
goto :eof

REM Проверка наличия Redis и RabbitMQ
:check_dependencies
call :log "Проверка зависимостей..."

kubectl get service redis >nul 2>&1
if %errorlevel% neq 0 (
    call :warn "Redis сервис не найден. Убедитесь, что Redis развернут в кластере."
    call :warn "Redis должен быть доступен по адресу 'redis:6379'"
) else (
    call :log "Redis найден"
)

kubectl get service rabbitmq >nul 2>&1
if %errorlevel% neq 0 (
    call :warn "RabbitMQ сервис не найден. Убедитесь, что RabbitMQ развернут в кластере."
    call :warn "RabbitMQ должен быть доступен по адресу 'rabbitmq:5672'"
) else (
    call :log "RabbitMQ найден"
)
goto :eof

REM Развертывание всей стеки
:deploy_all
call :log "Развертывание Maprox Pipe в Kubernetes..."

REM Проверка зависимостей
call :check_dependencies

REM Создание ConfigMap
call :log "Создание ConfigMap..."
kubectl apply -f configmap.yaml

call :log "Примечание: Secret 'rabbitmq' должен быть уже создан в кластере"

REM Развертывание основных компонентов
call :log "Развертывание балансировщика..."
kubectl apply -f balancer.yaml

call :log "Развертывание обработчика Galileo..."
kubectl apply -f galileo.yaml

call :log "Ожидание готовности всех компонентов..."
kubectl wait --for=condition=ready pod -l app=pipe-balancer -n o2 --timeout=300s
kubectl wait --for=condition=ready pod -l app=pipe-galileo -n o2 --timeout=300s

call :log "Развертывание завершено успешно!"
call :show_status
goto :eof

REM Удаление всей стеки
:delete_all
call :log "Удаление Maprox Pipe из Kubernetes..."

REM Удаление по частям
kubectl delete deployment pipe-galileo -n o2 --ignore-not-found=true
kubectl delete deployment pipe-balancer -n o2 --ignore-not-found=true

kubectl delete service pipe-galileo -n o2 --ignore-not-found=true
kubectl delete service pipe-galileo-nodeport -n o2 --ignore-not-found=true

kubectl delete configmap pipe-config -n o2 --ignore-not-found=true

call :log "Удаление завершено!"
goto :eof

REM Показать статус
:show_status
call :log "Статус развертывания:"
echo.

call :log "Pods:"
kubectl get pods -n o2

echo.
call :log "Services:"
kubectl get services -n o2

echo.
call :log "Deployments:"
kubectl get deployments -n o2

echo.
call :log "ConfigMaps и Secrets:"
kubectl get configmaps,secrets -n o2
goto :eof

REM Показать логи
:show_logs
if "%~1"=="" (
    call :error "Укажите имя сервиса для просмотра логов"
    echo Доступные сервисы:
    echo   - pipe-balancer
    echo   - pipe-galileo
    exit /b 1
)

call :log "Показ логов для %~1..."

if "%~1"=="pipe-balancer" (
    kubectl logs -f deployment/pipe-balancer -n o2
) else if "%~1"=="balancer" (
    kubectl logs -f deployment/pipe-balancer -n o2
) else if "%~1"=="pipe-galileo" (
    kubectl logs -f deployment/pipe-galileo -n o2
) else if "%~1"=="galileo" (
    kubectl logs -f deployment/pipe-galileo -n o2
) else (
    call :error "Неизвестный сервис: %~1"
    exit /b 1
)
goto :eof

REM Показать информацию о подключении
:show_connection_info
call :log "Информация о подключении:"
echo.

REM Получение NodePort для Galileo
for /f "tokens=*" %%i in ('kubectl get service pipe-galileo-nodeport -n o2 -o jsonpath^="{.spec.ports[0].nodePort}" 2^>nul') do set "nodeport=%%i"
if "!nodeport!"=="" set "nodeport=N/A"

echo 🌐 Внешний доступ:
echo   - Galileo Handler: NodePort !nodeport!
echo.

echo 🔧 Внутренние сервисы:
echo   - Redis: redis:6379 (должен быть развернут отдельно)
echo   - RabbitMQ: rabbitmq:5672 (должен быть развернут отдельно)
echo   - Galileo Handler: pipe-galileo:21001
echo.

echo 📊 Мониторинг:
echo   - kubectl get pods -n o2
echo   - kubectl logs -f deployment/pipe-galileo -n o2
echo.

echo ⚠️  Зависимости:
echo   - Redis и RabbitMQ должны быть развернуты в кластере
echo   - Redis должен быть доступен по адресу 'redis:6379'
echo   - RabbitMQ должен быть доступен по адресу 'rabbitmq:5672'
goto :eof

REM Основная функция
:main
if "%~1"=="" goto :show_help

call :check_kubectl

if "%~1"=="deploy" (
    call :deploy_all
) else if "%~1"=="delete" (
    call :delete_all
) else if "%~1"=="status" (
    call :show_status
) else if "%~1"=="logs" (
    call :show_logs "%~2"
) else if "%~1"=="info" (
    call :show_connection_info
) else if "%~1"=="help" (
    goto :show_help
) else (
    call :error "Неизвестная команда: %~1"
    echo Используйте 'deploy.cmd help' для справки
    exit /b 1
)
goto :eof

REM Показать справку
:show_help
echo Maprox Pipe - Kubernetes Deployment Script для Windows
echo.
echo Использование:
echo   %0 [команда] [параметры]
echo.
echo Команды:
echo   deploy          - Развертывание всей стеки
echo   delete          - Удаление всей стеки
echo   status          - Показать статус развертывания
echo   logs [service]  - Показать логи сервиса
echo   info            - Показать информацию о подключении
echo   help            - Показать эту справку
echo.
echo Примеры:
echo   %0 deploy                    # Развертывание всей стеки
echo   %0 logs galileo              # Логи обработчика Galileo
echo   %0 status                    # Статус развертывания
echo   %0 delete                    # Удаление всей стеки
echo.
echo Файлы:
echo   configmap.yaml               # Конфигурация
echo   balancer.yaml                # Балансировщик
echo   galileo.yaml                 # Обработчик Galileo
echo.
echo ⚠️  Важно:
echo   - Redis и RabbitMQ должны быть развернуты в кластере
echo   - Redis должен быть доступен по адресу 'redis:6379'
echo   - RabbitMQ должен быть доступен по адресу 'rabbitmq:5672'
echo   - Используется namespace 'o2'
goto :eof

REM Запуск основной функции
call :main %*
