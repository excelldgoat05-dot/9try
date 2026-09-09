class PaymentGatewayError(Exception):
    pass

class InsufficientFundsError(PaymentGatewayError):
    pass

class DuplicateTransactionError(PaymentGatewayError):
    pass

class WalletAssignmentError(PaymentGatewayError):
    pass
