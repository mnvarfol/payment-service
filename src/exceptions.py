class PaymentError(Exception):
    """
    Базовая ошибка платежного сервиса.
    """
    pass


class PaymentCreationError(PaymentError):
    """
    Ошибка создания платежа.
    """
    pass