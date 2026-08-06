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


class TreasuryEntityType(StrEnum):
    TENANT = "tenant"
    LEGAL_ENTITY = "legal_entity"
    BUSINESS_UNIT = "business_unit"


class CashPoolType(StrEnum):
    PHYSICAL = "physical"
    NOTIONAL = "notional"
    ZERO_BALANCE = "zero_balance"
    TARGET_BALANCE = "target_balance"


class CashPoolStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class TreasuryTransferStatus(StrEnum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    EXECUTED = "executed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    FAILED = "failed"


class FxExposureType(StrEnum):
    RECEIVABLE = "receivable"
    PAYABLE = "payable"
    FORECAST_INFLOW = "forecast_inflow"
    FORECAST_OUTFLOW = "forecast_outflow"
    LOAN = "loan"
    INVESTMENT = "investment"


class FxExposureStatus(StrEnum):
    OPEN = "open"
    PARTIALLY_HEDGED = "partially_hedged"
    FULLY_HEDGED = "fully_hedged"
    SETTLED = "settled"
    CANCELLED = "cancelled"


class HedgeInstrumentType(StrEnum):
    FORWARD = "forward"
    FUTURE = "future"
    OPTION = "option"
    SWAP = "swap"
    NATURAL_HEDGE = "natural_hedge"


class HedgeStatus(StrEnum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    ACTIVE = "active"
    MATURED = "matured"
    TERMINATED = "terminated"
    CANCELLED = "cancelled"


class DebtInstrumentType(StrEnum):
    TERM_LOAN = "term_loan"
    REVOLVING_CREDIT = "revolving_credit"
    OVERDRAFT = "overdraft"
    ISLAMIC_FINANCING = "islamic_financing"
    BOND = "bond"
    LEASE = "lease"


class DebtStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    MATURED = "matured"
    REPAID = "repaid"
    DEFAULTED = "defaulted"
    CANCELLED = "cancelled"


class TradeFinanceInstrumentType(StrEnum):
    LETTER_OF_CREDIT = "letter_of_credit"
    BANK_GUARANTEE = "bank_guarantee"
    STANDBY_LC = "standby_lc"


class TradeFinanceStatus(StrEnum):
    DRAFT = "draft"
    REQUESTED = "requested"
    ISSUED = "issued"
    AMENDED = "amended"
    UTILIZED = "utilized"
    EXPIRED = "expired"
    RELEASED = "released"
    CANCELLED = "cancelled"


class InvestmentType(StrEnum):
    TERM_DEPOSIT = "term_deposit"
    MONEY_MARKET = "money_market"
    GOVERNMENT_SECURITY = "government_security"
    SUKUK = "sukuk"
    MUTUAL_FUND = "mutual_fund"


class InvestmentStatus(StrEnum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    ACTIVE = "active"
    MATURED = "matured"
    REDEEMED = "redeemed"
    CANCELLED = "cancelled"


class StressScenarioType(StrEnum):
    LIQUIDITY_SHOCK = "liquidity_shock"
    FX_DEPRECIATION = "fx_depreciation"
    INTEREST_RATE_SHOCK = "interest_rate_shock"
    CUSTOMER_DEFAULT = "customer_default"
    SUPPLIER_DISRUPTION = "supplier_disruption"
    COMBINED = "combined"



class BudgetStatus(StrEnum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class BudgetType(StrEnum):
    ANNUAL = "annual"
    ROLLING = "rolling"
    CAPITAL = "capital"
    CASH_FLOW = "cash_flow"
    OPERATIONAL = "operational"


class BudgetVersionStatus(StrEnum):
    DRAFT = "draft"
    BASELINE = "baseline"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class PlanningScenario(StrEnum):
    BASE = "base"
    OPTIMISTIC = "optimistic"
    CONSERVATIVE = "conservative"
    STRESS = "stress"


class CostObjectType(StrEnum):
    CORPORATE = "corporate"
    FARM = "farm"
    BRANCH = "branch"
    DEPARTMENT = "department"
    COST_CENTRE = "cost_centre"
    PROFIT_CENTRE = "profit_centre"
    CROP = "crop"
    LIVESTOCK = "livestock"
    DAIRY = "dairy"
    POULTRY = "poultry"
    MANUFACTURING = "manufacturing"
    PROJECT = "project"


class CostAllocationMethod(StrEnum):
    FIXED_PERCENTAGE = "fixed_percentage"
    HEADCOUNT = "headcount"
    AREA = "area"
    PRODUCTION_VOLUME = "production_volume"
    REVENUE = "revenue"
    DIRECT_COST = "direct_cost"
    ACTIVITY_BASED = "activity_based"


class CostingMethod(StrEnum):
    ACTUAL = "actual"
    STANDARD = "standard"
    AVERAGE = "average"
    ACTIVITY_BASED = "activity_based"


class VarianceType(StrEnum):
    PRICE = "price"
    QUANTITY = "quantity"
    LABOUR_RATE = "labour_rate"
    LABOUR_EFFICIENCY = "labour_efficiency"
    OVERHEAD_SPENDING = "overhead_spending"
    OVERHEAD_VOLUME = "overhead_volume"
    SALES_VOLUME = "sales_volume"
    BUDGET_ACTUAL = "budget_actual"
