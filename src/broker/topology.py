from faststream.rabbit import (
    ExchangeType,
    RabbitExchange,
    RabbitQueue,
)


payments_exchange = RabbitExchange(
    name="payments.exchange",
    type=ExchangeType.TOPIC,
    durable=True,
)


payments_queue = RabbitQueue(
    name="payments.new",
    routing_key="payment.created",
    durable=True,
)


payments_retry_queue_1 = RabbitQueue(
    name="payments.retry.1",
    routing_key="payment.retry.1",
    durable=True,
    arguments={
        "x-message-ttl": 5_000,
        "x-dead-letter-exchange": "payments.exchange",
        "x-dead-letter-routing-key": "payment.created",
    },
)


payments_retry_queue_2 = RabbitQueue(
    name="payments.retry.2",
    routing_key="payment.retry.2",
    durable=True,
    arguments={
        "x-message-ttl": 10_000,
        "x-dead-letter-exchange": "payments.exchange",
        "x-dead-letter-routing-key": "payment.created",
    },
)


payments_retry_queue_3 = RabbitQueue(
    name="payments.retry.3",
    routing_key="payment.retry.3",
    durable=True,
    arguments={
        "x-message-ttl": 20_000,
        "x-dead-letter-exchange": "payments.exchange",
        "x-dead-letter-routing-key": "payment.created",
    },
)


payments_dlq = RabbitQueue(
    name="payments.dlq",
    routing_key="payment.dlq",
    durable=True,
)