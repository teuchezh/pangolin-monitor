# Интеграция Pangolin Monitor для Home Assistant

[🇷🇺 Русская версия](README.ru.md) | [🇺🇸 English Version](README.md)

![https://github.com/fosrl/pangolin](/images/logo.png)

Эта интеграция подключает Home Assistant к [Pangolin](https://github.com/fosrl/pangolin) для мониторинга туннелей.

![example](images/lovelace-card.png)

Ранее я использовал Cloudflare Zero Trust Tunnel, а после перехода на Pangolin понял, что мне не хватает мониторинга, поэтому решил быстро создать аддон для отслеживания статуса моих туннелей.  
Буду рад получить предложения по новой функциональности.

## Возможности

- Аутентификация по email и паролю
- Отслеживание туннелей/сайтов, зарегистрированных в Pangolin
- Отображение состояния (онлайн/оффлайн) и статистики по каждому туннелю
- Группировка сенсоров по устройствам
- Автоматическое обновление данных каждые 5 минут

## Требования

1. Администратор в Pangolin (обычный пользователь не может получать статусы туннелей)
2. HACS установлен в Home Assistant
3. У вас установлены [mushroom карты](https://github.com/piitaya/lovelace-mushroom) (опционально)

## Установка

1. Перейдите в Home Assistant → HACS
2. Нажмите на три точки в правом верхнем углу, выберите "Custom Repositories"
3. Вставьте URL этого репозитория в поле "Repository", измените тип на "Integrations" и нажмите "Add"
4. Перейдите в "Integrations"
5. Добавить новую интеграцию → Pangolin Monitor
6. Укажите ваш email Pangolin, пароль и базовый URL сервера

## Использование

### Встроенные компоненты

Если вы используете mushroom карты, можете использовать Jinja Generator скрипт ниже для автоматической генерации карт для всех ваших туннелей. Или можете использовать встроенный компонент "Tile" или любой другой компонент по вашему выбору.

![tile](images/tile.png)

```yaml
type: tile
entity: sensor.pangolin_tunnel_home_online
state_content:
  - state
  - megabytes_in
  - megabytes_out
```

### Jinja Generator скрипт для mushroom template карт
_Важно: Убедитесь, что ваши туннели настроены/видны перед выполнением этой части._

#### 🔧 Как использовать
1. Перейдите в Home Assistant → Developer Tools → Templates
2. Вставьте Jinja код ниже и скопируйте сгенерированный YAML в буфер обмена

```jinja
{% for entity in states.sensor 
     if entity.entity_id.startswith('sensor.pangolin_') %}
- type: custom:mushroom-template-card
  primary: Туннель {{ entity.attributes.site_name or entity.entity_id.split('_')[-1] }}
  secondary: >
    Статус: {{ '{{ states("' ~ entity.entity_id ~ '") }}' }}
    Входящий: {{ '{{ (state_attr("' ~ entity.entity_id ~ '", "megabytes_in") / 1024) | round(2) }} GB ·
    Исходящий: {{ (state_attr("' ~ entity.entity_id ~ '", "megabytes_out") / 1024) | round(2) }} GB' }}
  icon: mdi:cloud-outline
  icon_color: orange
  entity: {{ entity.entity_id }}
  layout: horizontal
  tap_action:
    action: more-info
{% endfor %}
```

3. Перейдите на ваш дашборд, отредактируйте и создайте новую карту как "Manual Card" (или в vertical-stack если карт несколько)
4. Вставьте сгенерированный код, затем добавьте следующее в начало кода:

```yaml
type: vertical-stack
cards:
```

_Примечание: убедитесь, что вставили код с правильными отступами._

## Сенсоры

Для каждого туннеля создаются следующие сенсоры:

### Traffic In (Входящий трафик)
- **Entity ID**: `sensor.{site_id}_traffic_in`
- **Единица измерения**: MB
- **Иконка**: 📥 mdi:download
- **Атрибуты**: 
  - `megabytes_in` - входящий трафик в MB
  - `megabytes_out` - исходящий трафик в MB
  - `site_name` - название туннеля
  - `site_type` - тип туннеля
  - `subnet` - подсеть
  - `address` - адрес
  - `version` - версия
  - `update_available` - доступно ли обновление

### Traffic Out (Исходящий трафик)
- **Entity ID**: `sensor.{site_id}_traffic_out`
- **Единица измерения**: MB
- **Иконка**: 📤 mdi:upload
- **Атрибуты**: те же, что и у Traffic In

### Online Status (Статус подключения)
- **Entity ID**: `sensor.{site_id}_online`
- **Значения**: "online" / "offline"
- **Device Class**: connectivity
- **Иконка**: ☁️ mdi:cloud-check (онлайн) / mdi:cloud-off (оффлайн)
- **Атрибуты**: те же, что и у Traffic In

## Группировка устройств

Все сенсоры автоматически группируются по устройствам:
- **Имя устройства**: название туннеля
- **Производитель**: Pangolin
- **Модель**: тип туннеля
- **Версия ПО**: версия туннеля

## Уведомления

Вы можете настроить уведомления при изменении статуса туннелей:

```yaml
automation:
  - alias: "Pangolin Tunnel Offline"
    trigger:
      - platform: state
        entity_id: sensor.pangolin_*
        to: "offline"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Туннель отключен"
          message: "{{ trigger.to_state.attributes.site_name }} перешел в режим offline"
```

## Отказ от ответственности

Этот проект не связан с Pangolin и не одобрен ими.

## Поддержка

Если у вас возникли проблемы:
1. Проверьте логи Home Assistant на наличие ошибок
2. Убедитесь, что у вас есть права администратора в Pangolin
3. Проверьте правильность URL, email и пароля
4. Создайте issue в этом репозитории с подробным описанием проблемы
