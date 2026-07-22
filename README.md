# Payment Service

Асинхронный сервис процессинга платежей.

Сервис реализует создание и обработку платежей с использованием FastAPI, PostgreSQL и RabbitMQ.

## Возможности

- Создание платежей
- Получение информации о платеже
- Авторизация через API Key (`X-API-Key`)
- Асинхронная обработка платежей через RabbitMQ
- Outbox Pattern для гарантированной публикации событий
- Retry-механизм через RabbitMQ TTL + Dead Letter Exchange
- Dead Letter Queue после неуспешных попыток обработки
- Idempotency Key для защиты от дублей
- Идемпотентная обработка сообщений consumer
- Отправка webhook уведомлений

---

# Запуск проекта

## 1. Клонировать репозиторий

```bash
git clone https://github.com/mnvarfol/payment-service.git

cd payment-service
```

---

## 2. Настроить переменные окружения

Скопировать пример файла окружения:

```bash
cp .env.example .env
```

При необходимости изменить значения переменных в `.env`.

---

## 3. Запустить сервисы

```bash
docker compose up -d --build
```

Проверить статус контейнеров:

```bash
docker compose ps
```

---

## 4. Выполнить миграции базы данных

```bash
docker compose exec api alembic upgrade head
```

---

# Доступные сервисы

| Сервис | URL |
|---|---|
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| RabbitMQ Management | http://localhost:15672 |

---

# Авторизация

Все API endpoints требуют API ключ.

Заголовок:

```http
X-API-Key: <значение из .env>
```

---

# API

## Создание платежа

### POST `/api/v1/payments`

Пример запроса:

```bash
curl -X POST \
'http://localhost:8000/api/v1/payments' \
-H 'accept: application/json' \
-H 'Idempotency-Key: 55' \
-H 'X-API-Key: super-secret-api-key' \
-H 'Content-Type: application/json' \
-d '{
  "amount": 1,
  "currency": "RUB",
  "description": "Test payment",
  "payment_metadata": {
    "order_id": "123"
  },
  "webhook_url": "https://example.com/"
}'
```

Ответ:

```json
{
  "payment_id": "53a0ee67-5397-465e-a6b2-8122d31c65da",
  "status": "pending",
  "created_at": "2026-07-22T06:15:22.143243Z"
}
```

---

## Получение платежа

### GET `/api/v1/payments/{payment_id}`

Пример запроса:

```bash
curl -X GET \
'http://localhost:8000/api/v1/payments/53a0ee67-5397-465e-a6b2-8122d31c65da' \
-H 'accept: application/json' \
-H 'X-API-Key: super-secret-api-key'
```

Ответ:

```json
{
  "payment_id": "53a0ee67-5397-465e-a6b2-8122d31c65da",
  "amount": "1",
  "currency": "RUB",
  "description": "Test payment",
  "status": "pending",
  "idempotency_key": "55",
  "webhook_url": "https://example.com/",
  "payment_metadata": {
    "order_id": "123"
  },
  "created_at": "2026-07-22T06:49:12.767Z"
}
```

---

# Архитектура

```
                 API
                  |
                  |
             PostgreSQL
                  |
          Payment + Outbox
                  |
                  |
          Outbox Publisher
                  |
                  |
            RabbitMQ Exchange
          payments.exchange
                  |
          payment.created
                  |
                  v

           payments.new

                  |
                  v

          Payment Consumer

             /          \
            /            \

       Success          Error

          |               |
          |               |
      Webhook        Retry queues

                         |
                  payments.retry.1
                         |
                       5 sec

                         |
                  payments.retry.2
                         |
                       10 sec

                         |
                  payments.retry.3
                         |
                       20 sec

                         |
                    payments.dlq
```

---

# Outbox Pattern

При создании платежа в рамках одной транзакции сохраняются:

- платеж (`payments`);
- событие (`outbox`).

Фоновый publisher:

1. Получает неопубликованные события.
2. Отправляет их в RabbitMQ.
3. Отмечает событие как опубликованное.

Это гарантирует публикацию событий даже при сбоях между записью в БД и отправкой сообщения в брокер.

---

# Retry механизм

Для повторной обработки сообщений используется RabbitMQ TTL + Dead Letter Exchange.

| Очередь | TTL |
|---|---:|
| `payments.retry.1` | 5 секунд |
| `payments.retry.2` | 10 секунд |
| `payments.retry.3` | 20 секунд |
| `payments.dlq` | без TTL |

После трёх неудачных попыток сообщение перемещается в Dead Letter Queue.

---

# Idempotency

Для защиты от повторного создания платежей используется заголовок:

```http
Idempotency-Key: <уникальный ключ>
```

Если клиент повторно отправляет запрос с тем же ключом, возвращается ранее созданный платеж.

---

# Webhook

После успешной обработки платежа сервис отправляет HTTP уведомление на указанный:

```
webhook_url
```