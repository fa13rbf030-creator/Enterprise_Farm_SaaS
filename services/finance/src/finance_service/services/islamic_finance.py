from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.models.islamic_finance import (
    IslamicAssessmentStatus,
    IslamicDisbursementEvidence,
    IslamicRuleStatus,
    LivestockZakatRule,
    NisabReference,
    SadaqahTransaction,
    ShariahRuleSet,
    UshrAssessment,
    ZakatAssessment,
)
from finance_service.repositories.islamic_finance import (
    get_shariah_rule_set,
)
from finance_service.schemas.islamic_finance import (
    IslamicDisbursementEvidenceCreate,
    LivestockZakatRuleCreate,
    NisabReferenceCreate,
    SadaqahTransactionCreate,
    ShariahRuleApprove,
    ShariahRuleSetCreate,
    UshrAssessmentCreate,
    ZakatAssessmentCreate,
)
from finance_service.services.islamic_finance_calculations import (
    calculate_crop_ushr,
    calculate_monetary_zakat,
    calculate_zakatable_base,
    is_hawl_complete,
)


class IslamicFinanceWorkflowError(ValueError):
    pass


async def create_shariah_rule_set(
    session: AsyncSession,
    *,
    payload: ShariahRuleSetCreate,
) -> ShariahRuleSet:
    obj = ShariahRuleSet(
        **payload.model_dump()
    )
    obj.rule_code = obj.rule_code.strip()
    obj.rule_name = obj.rule_name.strip()
    obj.notes = obj.notes.strip()

    session.add(obj)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise IslamicFinanceWorkflowError(
            "Shariah rule-set version already exists"
        ) from exc

    await session.refresh(obj)
    return obj


async def approve_shariah_rule_set(
    session: AsyncSession,
    *,
    rule_set_id,
    payload: ShariahRuleApprove,
) -> ShariahRuleSet:
    obj = await get_shariah_rule_set(
        session,
        tenant_id=payload.tenant_id,
        rule_set_id=rule_set_id,
        for_update=True,
    )

    if obj is None:
        raise IslamicFinanceWorkflowError(
            "Shariah rule-set not found"
        )

    if obj.status == IslamicRuleStatus.RETIRED:
        raise IslamicFinanceWorkflowError(
            "Retired rule-set cannot be approved"
        )

    obj.status = IslamicRuleStatus.APPROVED
    obj.approved_by = payload.approved_by
    obj.approved_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(obj)
    return obj


async def create_nisab_reference(
    session: AsyncSession,
    *,
    payload: NisabReferenceCreate,
) -> NisabReference:
    rule_set = await get_shariah_rule_set(
        session,
        tenant_id=payload.tenant_id,
        rule_set_id=payload.rule_set_id,
    )

    if rule_set is None:
        raise IslamicFinanceWorkflowError(
            "Shariah rule-set not found"
        )

    nisab_value = (
        payload.quantity * payload.unit_price
    )

    obj = NisabReference(
        tenant_id=payload.tenant_id,
        rule_set_id=payload.rule_set_id,
        reference_date=payload.reference_date,
        reference_type=payload.reference_type.strip(),
        quantity=payload.quantity,
        unit_price=payload.unit_price,
        nisab_value=nisab_value,
        currency_code=payload.currency_code.upper(),
    )

    session.add(obj)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise IslamicFinanceWorkflowError(
            "Nisab reference already exists for date"
        ) from exc

    await session.refresh(obj)
    return obj


async def create_zakat_assessment(
    session: AsyncSession,
    *,
    payload: ZakatAssessmentCreate,
) -> ZakatAssessment:
    rule_set = await get_shariah_rule_set(
        session,
        tenant_id=payload.tenant_id,
        rule_set_id=payload.rule_set_id,
    )

    if rule_set is None:
        raise IslamicFinanceWorkflowError(
            "Shariah rule-set not found"
        )

    if rule_set.status != IslamicRuleStatus.APPROVED:
        raise IslamicFinanceWorkflowError(
            "Zakat assessment requires approved Shariah rule-set"
        )

    base = calculate_zakatable_base(
        eligible_assets=payload.eligible_assets,
        deductible_liabilities=(
            payload.deductible_liabilities
        ),
    )

    hawl_complete = is_hawl_complete(
        holding_days=payload.holding_days,
        required_hawl_days=payload.required_hawl_days,
    )

    due = calculate_monetary_zakat(
        zakatable_base=base,
        nisab_value=payload.nisab_value,
        rate_percentage=payload.rate_percentage,
        hawl_complete=hawl_complete,
    )

    obj = ZakatAssessment(
        **payload.model_dump(),
        zakatable_base=base,
        zakat_due=due,
        status=IslamicAssessmentStatus.CALCULATED,
    )

    session.add(obj)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise IslamicFinanceWorkflowError(
            "Zakat assessment number already exists"
        ) from exc

    await session.refresh(obj)
    return obj


async def create_ushr_assessment(
    session: AsyncSession,
    *,
    payload: UshrAssessmentCreate,
) -> UshrAssessment:
    rule_set = await get_shariah_rule_set(
        session,
        tenant_id=payload.tenant_id,
        rule_set_id=payload.rule_set_id,
    )

    if rule_set is None:
        raise IslamicFinanceWorkflowError(
            "Shariah rule-set not found"
        )

    if rule_set.status != IslamicRuleStatus.APPROVED:
        raise IslamicFinanceWorkflowError(
            "Ushr assessment requires approved Shariah rule-set"
        )

    due = calculate_crop_ushr(
        eligible_crop_output_value=(
            payload.eligible_output_value
        ),
        rate_percentage=payload.rate_percentage,
    )

    obj = UshrAssessment(
        **payload.model_dump(),
        ushr_due=due,
        status=IslamicAssessmentStatus.CALCULATED,
    )

    session.add(obj)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise IslamicFinanceWorkflowError(
            "Ushr assessment number already exists"
        ) from exc

    await session.refresh(obj)
    return obj


async def create_livestock_zakat_rule(
    session: AsyncSession,
    *,
    payload: LivestockZakatRuleCreate,
) -> LivestockZakatRule:
    obj = LivestockZakatRule(
        **payload.model_dump()
    )
    obj.species_code = obj.species_code.strip()
    obj.obligation_unit = obj.obligation_unit.strip()
    obj.description = obj.description.strip()

    session.add(obj)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise IslamicFinanceWorkflowError(
            "Livestock Zakat rule already exists"
        ) from exc

    await session.refresh(obj)
    return obj


async def create_sadaqah_transaction(
    session: AsyncSession,
    *,
    payload: SadaqahTransactionCreate,
) -> SadaqahTransaction:
    obj = SadaqahTransaction(
        **payload.model_dump()
    )
    obj.transaction_number = obj.transaction_number.strip()
    obj.currency_code = obj.currency_code.upper()
    obj.purpose = obj.purpose.strip()

    session.add(obj)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise IslamicFinanceWorkflowError(
            "Sadaqah transaction number already exists"
        ) from exc

    await session.refresh(obj)
    return obj


async def create_disbursement_evidence(
    session: AsyncSession,
    *,
    payload: IslamicDisbursementEvidenceCreate,
) -> IslamicDisbursementEvidence:
    obj = IslamicDisbursementEvidence(
        **payload.model_dump()
    )
    obj.evidence_number = obj.evidence_number.strip()
    obj.notes = obj.notes.strip()

    session.add(obj)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise IslamicFinanceWorkflowError(
            "Disbursement evidence number already exists"
        ) from exc

    await session.refresh(obj)
    return obj
