# Kubernetes Deployment Script for Maprox Pipe
# PowerShell version

param(
    [string]$Action = "help"
)

# Colors for output
$Colors = @{
    Info = "Green"
    Warning = "Yellow"
    Error = "Red"
    Success = "Cyan"
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Colors[$Color]
}

function Show-Help {
    Write-ColorOutput "Использование: .\deploy.ps1 [действие]" "Info"
    Write-ColorOutput ""
    Write-ColorOutput "Действия:" "Info"
    Write-ColorOutput "  deploy     - Развернуть все компоненты" "Success"
    Write-ColorOutput "  delete     - Удалить все компоненты" "Warning"
    Write-ColorOutput "  restart    - Перезапустить все компоненты" "Info"
    Write-ColorOutput "  logs       - Показать логи" "Info"
    Write-ColorOutput "  status     - Показать статус" "Info"
    Write-ColorOutput "  info       - Показать информацию о подключении" "Info"
    Write-ColorOutput "  help       - Показать эту справку" "Info"
    Write-ColorOutput ""
    Write-ColorOutput "Примеры:" "Info"
    Write-ColorOutput "  .\deploy.ps1 deploy" "Success"
    Write-ColorOutput "  .\deploy.ps1 logs" "Success"
}

function Check-Dependencies {
    Write-ColorOutput "Проверка зависимостей..." "Info"
    
    # Проверяем kubectl
    try {
        $kubectlVersion = kubectl version --client --short 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✓ kubectl найден: $kubectlVersion" "Success"
        } else {
            Write-ColorOutput "✗ kubectl не найден или не работает" "Error"
            return $false
        }
    } catch {
        Write-ColorOutput "✗ kubectl не найден" "Error"
        return $false
    }
    
    # Проверяем подключение к кластеру
    try {
        $clusterInfo = kubectl cluster-info 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✓ Подключение к кластеру установлено" "Success"
        } else {
            Write-ColorOutput "✗ Не удается подключиться к кластеру" "Error"
            return $false
        }
    } catch {
        Write-ColorOutput "✗ Не удается подключиться к кластеру" "Error"
        return $false
    }
    
    # Проверяем namespace o2
    try {
        $namespace = kubectl get namespace o2 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✓ Namespace 'o2' существует" "Success"
        } else {
            Write-ColorOutput "✗ Namespace 'o2' не найден. Создайте его командой: kubectl create namespace o2" "Error"
            return $false
        }
    } catch {
        Write-ColorOutput "✗ Не удается проверить namespace 'o2'" "Error"
        return $false
    }
    
    # Проверяем секрет rabbitmq
    try {
        $secret = kubectl get secret rabbitmq -n o2 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✓ Секрет 'rabbitmq' найден в namespace 'o2'" "Success"
        } else {
            Write-ColorOutput "✗ Секрет 'rabbitmq' не найден в namespace 'o2'. Убедитесь, что он создан." "Error"
            return $false
        }
    } catch {
        Write-ColorOutput "✗ Не удается проверить секрет 'rabbitmq'" "Error"
        return $false
    }
    
    return $true
}

function Deploy-All {
    Write-ColorOutput "Развертывание всех компонентов..." "Info"
    
    if (-not (Check-Dependencies)) {
        Write-ColorOutput "Проверка зависимостей не пройдена. Прерывание." "Error"
        return
    }
    
    # Применяем ConfigMap
    Write-ColorOutput "Применение ConfigMap..." "Info"
    kubectl apply -f configmap.yaml -n o2
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "Ошибка при применении ConfigMap" "Error"
        return
    }
    
    # Применяем balancer
    Write-ColorOutput "Развертывание balancer..." "Info"
    kubectl apply -f balancer.yaml -n o2
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "Ошибка при развертывании balancer" "Error"
        return
    }
    
    # Применяем galileo handler
    Write-ColorOutput "Развертывание Galileo handler..." "Info"
    kubectl apply -f galileo.yaml -n o2
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "Ошибка при развертывании Galileo handler" "Error"
        return
    }
    
    Write-ColorOutput "Все компоненты успешно развернуты!" "Success"
    Write-ColorOutput "Проверьте статус командой: .\deploy.ps1 status" "Info"
}

function Remove-All {
    Write-ColorOutput "Удаление всех компонентов..." "Warning"
    
    # Удаляем galileo handler
    Write-ColorOutput "Удаление Galileo handler..." "Info"
    kubectl delete -f galileo.yaml -n o2 2>$null
    
    # Удаляем balancer
    Write-ColorOutput "Удаление balancer..." "Info"
    kubectl delete -f balancer.yaml -n o2 2>$null
    
    # Удаляем ConfigMap
    Write-ColorOutput "Удаление ConfigMap..." "Info"
    kubectl delete -f configmap.yaml -n o2 2>$null
    
    Write-ColorOutput "Все компоненты удалены!" "Success"
}

function Restart-All {
    Write-ColorOutput "Перезапуск всех компонентов..." "Info"
    
    Remove-All
    Start-Sleep -Seconds 5
    Deploy-All
}

function Show-Logs {
    Write-ColorOutput "Логи компонентов (Ctrl+C для выхода):" "Info"
    Write-ColorOutput ""
    Write-ColorOutput "Balancer:" "Success"
    kubectl logs -f deployment/pipe-balancer -n o2
}

function Show-Status {
    Write-ColorOutput "Статус развертываний:" "Info"
    kubectl get deployments -n o2
    
    Write-ColorOutput ""
    Write-ColorOutput "Статус подов:" "Info"
    kubectl get pods -n o2
    
    Write-ColorOutput ""
    Write-ColorOutput "Статус сервисов:" "Info"
    kubectl get services -n o2
}

function Show-ConnectionInfo {
    Write-ColorOutput "Информация о подключении:" "Info"
    
    # Получаем IP и порт для Galileo handler
    try {
        $galileoService = kubectl get service pipe-galileo-nodeport -n o2 -o jsonpath='{.spec.ports[0].nodePort}' 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "Galileo Handler доступен на порту: $galileoService" "Success"
            Write-ColorOutput "Подключение: telnet localhost $galileoService" "Info"
        } else {
            Write-ColorOutput "Galileo Handler не развернут или недоступен" "Warning"
        }
    } catch {
        Write-ColorOutput "Не удается получить информацию о Galileo Handler" "Warning"
    }
    
    # Получаем информацию о Redis и RabbitMQ
    Write-ColorOutput ""
    Write-ColorOutput "Redis доступен по адресу: redis:6379" "Info"
    Write-ColorOutput "RabbitMQ доступен по адресу: rabbitmq:5672" "Info"
}

# Основная логика
switch ($Action.ToLower()) {
    "deploy" { Deploy-All }
    "delete" { Remove-All }
    "restart" { Restart-All }
    "logs" { Show-Logs }
    "status" { Show-Status }
    "info" { Show-ConnectionInfo }
    "help" { Show-Help }
    default { 
        Write-ColorOutput "Неизвестное действие: $Action" "Error"
        Show-Help
    }
}
