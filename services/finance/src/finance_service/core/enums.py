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
    BANK_RECONCILIATION = "bank_reconciliation"


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


class BankAccountStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CLOSED = "closed"


class BankAccountType(StrEnum):
    CURRENT = "current"
    SAVINGS = "savings"
    CASH = "cash"
    PETTY_CASH = "petty_cash"
    MOBILE_WALLET = "mobile_wallet"


class BankStatementStatus(StrEnum):
    DRAFT = "draft"
    IMPORTED = "imported"
    IN_RECONCILIATION = "in_reconciliation"
    RECONCILED = "reconciled"
    VOID = "void"


class BankStatementLineType(StrEnum):
    CREDIT = "credit"
    DEBIT = "debit"


class ReconciliationStatus(StrEnum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReconciliationMatchType(StrEnum):
    EXACT = "exact"
    PARTIAL = "partial"
    MANUAL = "manual"
    BANK_CHARGE = "bank_charge"
    BANK_INTEREST = "bank_interest"


class TreasuryPaymentBatchStatus(StrEnum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    GENERATED = "generated"
    SUBMITTED = "submitted"
    PARTIALLY_SETTLED = "partially_settled"
    SETTLED = "settled"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TreasuryPaymentItemStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUBMITTED = "submitted"
    SETTLED = "settled"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TreasuryApprovalDecision(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"


class TreasuryFileFormat(StrEnum):
    ISO20022_PAIN_001 = "iso20022_pain_001"
    CSV = "csv"
    FIXED_WIDTH = "fixed_width"
    BANK_API = "bank_api"


class SettlementStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    RETURNED = "returned"


class LiquidityForecastScenario(StrEnum):
    BASE = "base"
    CONSERVATIVE = "conservative"
    STRESS = "stress"


class FraudCheckStatus(StrEnum):
    PASSED = "passed"
    REVIEW_REQUIRED = "review_required"
    BLOCKED = "blocked"
