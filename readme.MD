## Начальная реализация домашнего задания

Данная реализация не выполняет требования по Maintainability, Reliability, Scalability.

Требуется на основе имеющейся заготовки спроектировать и реализовать подходящую архитектуру с учетом требований из таблички.

## Описание

Здесь находится приложение для аренды самокатов.
В нем разместилось всего три метода:
- Создание оффера
- Создание заказа
- Завершение заказа

Основная логика приложения находится в main.py:
- Содержит основные функции бизнес-логики для работы с сущностями.
- Использует словари в памяти как “базу данных”.
- Содержит тестовые сценарии.

В data_requests.py реализованы функции для получения данных из внешних сервисов через HTTP-запросы. Использует библиотеку requests для HTTP-коммуникации.

Модели данных в models.py определяют объекты передачи данных (DTO).

Заглушки API. В fastapi_stubs.py реализован сервер FastAPI с эндпоинтами, имитирующими внешние сервисы. В эти сервисы поступают запросы из data_requests.py.

## Параметры

1. X – число одновременно создаваемых заказов -- внешняя нагрузка. Измеряется в RPS.
2. Y – сколько раз пользователь просматривал информацию о заказе в приложении. Число показов в среднем на один заказ.
3. Z – размер записи о заказе в базе. Измеряется в байтах.

Источники данных:
- scooters - Самокаты
- tariff-zones - Тарифные зоны
- users – Пользователи
- configs – Конфигурация

Есть также сервис платежей – payments.

## Новая структура

- `app/api` — схемы и HTTP-маршруты FastAPI.
- `app/services` — бизнес-логика офферов/заказов.
- `app/clients` — вызовы внешних сервисов.
- `app/utils` — общие утилиты (подпись офферов).
- `app/main.py` — создание FastAPI-приложения.
- `stubs/fastapi_stubs.py` — заглушки внешних сервисов для локального запуска.
- `app/repository` — слой работы с БД (инициализация пула, CRUD-хелперы).
- `migrations/` — SQL-меграции (инициализация таблиц/партиционирования).
- `app/Dockerfile` и `app/requirements.txt` — контейнер API.
- `stubs/Dockerfile` и `stubs/requirements.txt` — контейнер заглушек.
- `tests/Dockerfile` и `tests/requirements.txt` — контейнер для интеграционных сценариев.

## Запуск через Docker Compose

```bash
docker-compose up --build
```

Поднимет API на `http://localhost:8000` и заглушки внешних сервисов на `http://localhost:3629`.
Контейнер `tests` выполняет простой интеграционный прогон (создание/завершение двух заказов).

### Полный цикл с пересборкой/очисткой данных

```bash
# остановить и удалить volume с БД (если нужно прогнать миграции с нуля)
docker compose down --rmi all --volumes --remove-orphans

# !!!!! Если вдруг хотите снести все что docker у вас на машинке насоздавал и закешировал !!!!!
docker system prune -af --volumes

# собрать образы заново и поднять стек
docker compose up --build
```

Стек включает:
- `db` — Postgres 16 с `pg_partman` и `pg_cron`, миграции из `migrations/`.
- `stubs` — заглушки внешних сервисов.
- `api` — FastAPI-приложение `app.main:app`.
- `tests` — контейнер с pytest, выполняет интеграционный сценарий.

## Запуск без Docker (локальный Postgres + pipenv). Для анти-докеров

1. Установить зависимости:
   ```bash
   pipenv install
   pipenv shell
   ```
2. Поднять локальный Postgres (нужен установленный PostgreSQL):
   ```bash
   chmod +x scripts/start_local_pg.sh
   ./scripts/start_local_pg.sh
   export DATABASE_URL=postgresql://superscooters:superscooters@127.0.0.1:5432/superscooters
   ```
3. Запустить заглушки:
   ```bash
   python stubs/fastapi_stubs.py
   ```
4. В другой консоли (в том же `pipenv shell`) поднять API:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
5. (Опционально) Прогнать тесты:
   ```bash
   pytest
   ```

## База данных

- Postgres 16 c расширениями `pg_partman` для ежедневного партиционирования таблицы `orders`.
- Миграции (`migrations/001_init.sql`) создают таблицы `orders` (партиционированная) и `user_summary`, настраивают partman и cron-задачу `partman.run_maintenance()`.
- Переменная окружения `DATABASE_URL` задаёт строку подключения, по умолчанию `postgresql://superscooters:superscooters@db:5432/superscooters` в docker-compose.
