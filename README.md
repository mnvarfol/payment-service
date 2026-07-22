# payment-service
Асинхронный сервис процессинга платежей

# Запуск проекта

## 1. Клонировать репозиторий
git clone https://github.com/mnvarfol/payment-service.git
cd payment-service

## 2. Настроить переменные окружения (скопировать пример файла окружения и при необходимости изменить значения в .env)
cp .env.example .env

## 3. Запустить сервисы и проверить их статус
docker compose up -d --build
docker compose ps

## 4. Выполнить миграции базы данных
docker compose exec api alembic upgrade head

Доступные сервисы:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- RabbitMQ Management: http://localhost:15672

Авторизация:
Все API endpoints требуют заголовок X-API-Key: <значение из .env>

API:

    Создание платежа POST /api/v1/payments
        Пример:
        curl -X 'POST' \
        'http://127.0.0.1:8000/api/v1/payments' \
        -H 'accept: application/json' \
        -H 'Idempotency-Key: 55' \
        -H 'X-API-Key: super-secret-api-key' \
        -H 'Content-Type: application/json' \
        -d '{
        "amount": 1,
        "currency": "RUB",
        "description": "string",
        "payment_metadata": {
            "additionalProp1": {}
        },
        "webhook_url": "https://example.com/"
        }'

        Ответ:
        {
        "payment_id": "53a0ee67-5397-465e-a6b2-8122d31c65da",
        "status": "pending",
        "created_at": "2026-07-22T06:15:22.143243Z"
        }

    Получение платежа GET /api/v1/payments/{payment_id}
        Пример:
        curl -X 'GET' \
        'http://127.0.0.1:8000/api/v1/payments/53a0ee67-5397-465e-a6b2-8122d31c65da' \
        -H 'accept: application/json' \
        -H 'X-API-Key: super-secret-api-key'

        Ответ:
        {
        "payment_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "amount": "1",
        "currency": "RUB",
        "description": "string",
        "status": "pending",
        "idempotency_key": "string",
        "webhook_url": "string",
        "payment_metadata": {
            "additionalProp1": {}
        },
        "created_at": "2026-07-22T06:49:12.767Z"
        }

Outbox Pattern:
    При создании платежа в одной транзакции сохраняются:

    платеж (payments);
    событие (outbox_events).

    Фоновый publisher:

    получает неопубликованные события;
    отправляет их в RabbitMQ;
    отмечает событие как опубликованное

Retry механизм:
    Для повторной обработки сообщений используется RabbitMQ TTL + Dead Letter Exchange
    - payments.retry.1 - 5 секунд
    - payments.retry.2 - 10 секунд
    - payments.retry.3 - 20 секунд
    - payments.dlq - без TTL

Idempotency:
Для защиты от повторного создания платежей используется заголовок Idempotency-Key. При повторном запросе с тем же ключом возвращается ранее созданный платеж.

Webhook:
После успешной обработки платежа отправляется HTTP уведомление на указанный webhook_url.