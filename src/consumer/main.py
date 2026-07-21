from faststream import FastStream

from src.broker.rabbit import broker
from src.consumer import handlers  # noqa: F401

app = FastStream(broker)