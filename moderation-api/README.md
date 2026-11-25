# API модерации объявлений

## Запуск

Выполни команды из папки `moderation-api`. Проект проверен на Python 3.12.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install --no-deps -r requirements-pgmigrate.txt
fastapi dev
```

Интерактивная документация открывается по адресу <http://127.0.0.1:8000/docs>.

## Запрос

`POST /predict` принимает JSON со всеми семью полями.

```sh
curl -X POST http://127.0.0.1:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{
    "seller_id": 12,
    "is_verified_seller": false,
    "item_id": 42,
    "name": "Настольная лампа",
    "description": "Лампа в хорошем состоянии",
    "category": 3,
    "images_qty": 0
  }'
```

Сервис вернет HTTP `200` и JSON-значение `true`. Оно означает, что найдено нарушение. У подтвержденного продавца результат всегда `false`. Для неподтвержденного продавца результат `false`, если есть хотя бы одно изображение.

- Сервис возвращает `400`, если в JSON есть синтаксическая ошибка, тело запроса отсутствует или данные не соответствуют схеме. Например, пропущено обязательное поле, указан неверный тип или количество изображений отрицательное. Детали находятся в поле `detail`.
- Сервис возвращает `500`, если при проверке произошла внутренняя ошибка. Ответ содержит `{"detail": "Internal server error"}`.

В `main.py` собирается приложение. Обработчик в `routers/predict.py` принимает запрос и формирует HTTP-ответ. Репозиторий в `repository.py` возвращает минимум фотографий для продавца. Сервис в `service.py` сравнивает количество фотографий с этим минимумом.

## Тесты

```sh
python -m pytest -q
```

Также можно запускать тесты напрямую.

```sh
pytest -q
```


## ДЗ 3: PostgreSQL и предсказание по идентификатору

Все команды выполняются из `moderation-api`, Python 3.12. При переносе проекта
создай `.venv` заново командами выше. Docker Desktop должен быть запущен.

```sh
docker compose up
```

Оставь эту команду работающей. В другом терминале из той же папки:

```sh
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install --no-deps -r requirements-pgmigrate.txt
pgmigrate -d db -t latest migrate
fastapi dev
```

`requirements-pgmigrate.txt` устанавливается с `--no-deps`: мигратор требует
пакет `psycopg2`, а курс использует его готовую бинарную сборку
`psycopg2-binary`. Остальные зависимости мигратора (`sqlparse`, `PyYAML`)
указаны в основном `requirements.txt`. Это исключает сборку драйвера и
установку системных заголовков PostgreSQL.

Конфигурация миграций — `db/migrations.yml`. PostgreSQL 16 доступен на
`localhost:5435`, база `hw`, пользователь и пароль `postgres`.
Повторная команда миграции не применяет уже выполненные миграции.
Данные хранятся в томе `pg_data`; `docker compose down` сохраняет том.

### Схема и репозитории

`users`: `id`, `first_name`, `last_name`, `is_verified`, `violations_qty`.
`advertisements`: `id`, `seller_id`, `name`, `description`, `category`, `images_qty`.
Связь один ко многим: `advertisements.seller_id` ссылается на `users.id`.
Все поля обязательны; количества неотрицательны. ID генерируются через `SERIAL`.
Категория хранится как целое число: перечня категорий в задании нет.

`UserRepository.create` и `AdvertisementRepository.create` создают записи и
возвращают ID. `AdvertisementRepository.get_for_prediction` получает все семь
полей прежней схемы одним SQL-запросом с `JOIN users`. SQL использует плейсхолдеры.
`SimplePredictionService` проверяет наличие объявления и вызывает прежний
`ModerationService`. `violations_qty` хранится, но не меняет правило из ДЗ 1.
Соединение `asyncpg` открывается на запрос и закрывается после него.

### Новый запрос

Допущение: используем POST, как у `/predict`, и query-параметр, как в сигнатуре
`simple_predict(item_id: int)` из задания. Тело JSON для этой ручки не требуется.

```sh
curl -X POST 'http://127.0.0.1:8000/simple_predict?item_id=42'
```

- `200` и JSON `true` либо `false` — тот же формат и правило, что у `/predict`.
- `400` — обязательный `item_id` отсутствует, не является целым или выходит за
  диапазон `1..2147483647` (положительный ID, помещающийся в PostgreSQL INTEGER).
- `404` и `{"detail": "Advertisement not found"}` — объявления нет в БД.
- `500` и `{"detail": "Internal server error"}` — ошибка получения данных или предсказания.

Пример данных для ручной проверки (через psql внутри контейнера):

```sh
docker compose exec postgres psql -U postgres -d hw
```

```sql
INSERT INTO users (first_name, last_name, is_verified, violations_qty)
VALUES ('Анна', 'Иванова', false, 0) RETURNING id;
-- Подставь полученный ID вместо 1.
INSERT INTO advertisements (seller_id, name, description, category, images_qty)
VALUES (1, 'Лампа', 'Рабочая лампа', 3, 0) RETURNING id;
```

Для curl используй ID из второго INSERT.

### Проверки ДЗ 3

После запуска PostgreSQL и миграций:

```sh
pytest
python -m pytest
```

Старые тесты `/predict` сохранены. Новые тесты проверяют оба результата и
совпадение с `/predict`, входные значения и границы, отсутствие записи,
ошибки сервиса и запроса к БД, создание пользователей и объявлений,
внешний ключ и неотрицательные количества. Данные создаются фикстурами в
транзакции, которая откатывается после каждого теста. Таблицы не очищаются,
существующие данные сохраняются; последовательности ID могут увеличиваться.
Тесты используют настоящую PostgreSQL и не пропускаются при ее недоступности.
