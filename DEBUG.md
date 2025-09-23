# Отладка интеграции Pangolin Monitor

## Включение расширенного логирования

Для диагностики проблем с интеграцией добавлено расширенное логирование. Чтобы увидеть подробные логи:

### 1. Включите логирование в configuration.yaml

```yaml
logger:
  default: info
  logs:
    custom_components.pangolin_monitor: debug
```

### 2. Перезапустите Home Assistant

После изменения configuration.yaml перезапустите Home Assistant.

### 3. Попробуйте настроить интеграцию

1. Перейдите в **Настройки** → **Устройства и службы**
2. Нажмите **Добавить интеграцию**
3. Найдите **Pangolin Monitor**
4. Введите ваши данные

### 4. Проверьте логи

После попытки настройки проверьте логи:

1. Перейдите в **Настройки** → **Система** → **Журналы**
2. Или используйте **Developer Tools** → **Logs**
3. Найдите записи с префиксом `custom_components.pangolin_monitor`

## Что показывают логи

### При настройке интеграции:
- `Starting validation with data` - начало проверки данных
- `Attempting login to` - попытка входа в систему
- `Login response status` - статус ответа сервера
- `Token received` - получение токена
- `Testing sites access` - проверка доступа к сайтам
- `Validation completed successfully` - успешное завершение

### При загрузке интеграции:
- `Setting up Pangolin Monitor integration` - начало настройки
- `Created API client, attempting authentication` - создание API клиента
- `Authentication successful` - успешная аутентификация
- `Setting up sensors` - создание сенсоров
- `Found X sites in coordinator data` - количество найденных сайтов

### При обновлении данных:
- `Getting sites data` - получение данных о сайтах
- `Sites response status` - статус ответа API
- `Found X sites in response` - количество сайтов в ответе
- `Processed site: Name (ID: X, Online: Y)` - обработка каждого сайта

## Типичные ошибки и их решения

### "CSRF token missing or invalid" (статус 403)
- **Исправлено в версии 0.1.8**: Интеграция использует фиксированный CSRF токен `x-csrf-protection`
- Этот токен соответствует тому, что используется в Postman и других клиентах

### "Authentication failed: Invalid credentials"
- Проверьте правильность email и пароля
- Убедитесь, что у пользователя есть права администратора в Pangolin

### "Connection error"
- Проверьте правильность Base URL
- Убедитесь, что сервер Pangolin доступен
- Проверьте сетевое соединение

### "No token received during authentication"
- **Исправлено в версии 0.1.10**: Интеграция теперь поддерживает cookie-based аутентификацию
- Сервер Pangolin использует cookies вместо JWT токенов в JSON ответе
- Токен передается через cookie `p_session_token`

### "Failed to parse response as JSON"
- Сервер вернул не JSON ответ
- Возможно, сервер недоступен или возвращает ошибку

### "No sites found"
- У пользователя нет доступа к сайтам
- Нужны права администратора в Pangolin

### "CSRF request failed"
- Проблема с получением CSRF токена
- Проверьте доступность сервера Pangolin
- Возможно, изменился API эндпоинт

## Отправка логов для поддержки

Если проблема не решается, отправьте следующие данные:

1. Полные логи с префиксом `custom_components.pangolin_monitor`
2. Версию Home Assistant
3. Версию интеграции
4. Версию Pangolin сервера
5. Описание проблемы

## Временное отключение логирования

После решения проблемы отключите расширенное логирование:

```yaml
logger:
  default: info
  logs:
    custom_components.pangolin_monitor: warning
```

Или удалите секцию `logs` полностью.
