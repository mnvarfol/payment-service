from faststream.rabbit import (
    ExchangeType,
    RabbitExchange,
    RabbitQueue,
)


payments_exchange = RabbitExchange(
    name="payments.exchange",
    type=ExchangeType.TOPIC,
)


payments_queue = RabbitQueue(
    name="payments.new",
    routing_key="payment.*",
)