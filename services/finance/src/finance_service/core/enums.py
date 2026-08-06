from enum import StrEnum


class AccountType(StrEnum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class NormalBalance(StrEnum):
    DEBIT = "debit"
    CREDIT = "credit"


class AccountStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class FiscalPeriodStatus(StrEnum):
    OPEN = "open"
    SOFT_CLOSED = "soft_closed"
    CLOSED = "closed"


class JournalStatus(StrEnum):
    DRAFT = "draft"
    POSTED = "posted"
    REVERSED = "reversed"
    VOID = "void"


class JournalSource(StrEnum):
    MANUAL = "manual"
    ACCOUNTS_RECEIVABLE = "accounts_receivable"
    ACCOUNTS_PAYABLE = "accounts_payable"
    INVENTORY = "inventory"
    PAYROLL = "payroll"
    AGRICULTURE = "agriculture"
    MANUFACTURING = "manufacturing"
    SYSTEM = "system"


class BalanceDirection(StrEnum):
    DEBIT = "debit"
    CREDIT = "credit"
    ZERO = "zero"


class PeriodAction(StrEnum):
    OPEN = "open"
    SOFT_CLOSE = "soft_close"
    CLOSE = "close"
    REOPEN = "reopen"


class OpeningBalanceStatus(StrEnum):
    DRAFT = "draft"
    VALIDATED = "validated"
    POSTED = "posted"
    REJECTED = "rejected"


class FiscalYearCloseStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    FAILED = "failed"


class CustomerStatus(StrEnum):
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    INACTIVE = "inactive"


class InvoiceStatus(StrEnum):
    DRAFT = "draft"
    ISSUED = "issued"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    VOID = "void"
    CREDITED = "credited"


class CreditNoteStatus(StrEnum):
    DRAFT = "draft"
    ISSUED = "issued"
    APPLIED = "applied"
    VOID = "void"


class ReceiptStatus(StrEnum):
    DRAFT = "draft"
    POSTED = "posted"
    PARTIALLY_ALLOCATED = "partially_allocated"
    ALLOCATED = "allocated"
    VOID = "void"


class PaymentMethod(StrEnum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CHEQUE = "cheque"
    CARD = "card"
    MOBILE_WALLET = "mobile_wallet"
    OTHER = "other"


class VendorStatus(StrEnum):
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    INACTIVE = "inactive"


class SupplierInvoiceStatus(StrEnum):
    DRAFT = "draft"
    POSTED = "posted"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    VOID = "void"
    DEBITED = "debited"


class DebitNoteStatus(StrEnum):
    DRAFT = "draft"
    ISSUED = "issued"
    APPLIED = "applied"
    VOID = "void"


class VendorPaymentStatus(StrEnum):
    DRAFT = "draft"
    POSTED = "posted"
    PARTIALLY_ALLOCATED = "partially_allocated"
    ALLOCATED = "allocated"
    VOID = "void"
