from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.models.tax_compliance import (
    StatutoryFiling,
    TaxCode,
    TaxJurisdiction,
    TaxPeriod,
    TaxRate,
    TaxRegistration,
    TaxReturn,
    WithholdingTaxRule,
)
from finance_service.repositories.tax_compliance import (
    get_tax_jurisdiction,
    get_tax_registration,
    get_tax_period,
)
from finance_service.schemas.tax_compliance import (
    StatutoryFilingCreate,
    TaxCodeCreate,
    TaxJurisdictionCreate,
    TaxPeriodCreate,
    TaxRateCreate,
    TaxRegistrationCreate,
    TaxReturnCreate,
    WithholdingTaxRuleCreate,
)
from finance_service.services.tax_compliance_calculations import (
    calculate_net_tax_liability,
)


class TaxComplianceWorkflowError(ValueError):
    pass


async def create_tax_jurisdiction(
    session: AsyncSession,
    *,
    payload: TaxJurisdictionCreate,
) -> TaxJurisdiction:
    obj = TaxJurisdiction(
        tenant_id=payload.tenant_id,
        jurisdiction_code=payload.jurisdiction_code.strip(),
        jurisdiction_name=payload.jurisdiction_name.strip(),
        country_code=payload.country_code.upper(),
        region_code=payload.region_code,
        authority_name=payload.authority_name.strip(),
        authority_reference=payload.authority_reference,
    )
    session.add(obj)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise TaxComplianceWorkflowError(
            "Tax jurisdiction already exists"
        ) from exc

    await session.refresh(obj)
    return obj


async def create_tax_registration(
    session: AsyncSession,
    *,
    payload: TaxRegistrationCreate,
) -> TaxRegistration:
    jurisdiction = await get_tax_jurisdiction(
        session,
        tenant_id=payload.tenant_id,
        jurisdiction_id=payload.jurisdiction_id,
    )
    if jurisdiction is None:
        raise TaxComplianceWorkflowError(
            "Tax jurisdiction not found"
        )

    obj = TaxRegistration(
        tenant_id=payload.tenant_id,
        jurisdiction_id=payload.jurisdiction_id,
        registration_number=payload.registration_number.strip(),
        legal_name=payload.legal_name.strip(),
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
    )
    session.add(obj)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise TaxComplianceWorkflowError(
            "Tax registration already exists"
        ) from exc

    await session.refresh(obj)
    return obj


async def create_tax_code(
    session: AsyncSession,
    *,
    payload: TaxCodeCreate,
) -> TaxCode:
    jurisdiction = await get_tax_jurisdiction(
        session,
        tenant_id=payload.tenant_id,
        jurisdiction_id=payload.jurisdiction_id,
    )
    if jurisdiction is None:
        raise TaxComplianceWorkflowError(
            "Tax jurisdiction not found"
        )

    obj = TaxCode(**payload.model_dump())
    obj.tax_code = obj.tax_code.strip()
    obj.tax_name = obj.tax_name.strip()

    session.add(obj)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise TaxComplianceWorkflowError(
            "Tax code already exists"
        ) from exc

    await session.refresh(obj)
    return obj


async def create_tax_rate(
    session: AsyncSession,
    *,
    payload: TaxRateCreate,
) -> TaxRate:
    obj = TaxRate(**payload.model_dump())
    session.add(obj)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise TaxComplianceWorkflowError(
            "Tax rate already exists for effective date"
        ) from exc

    await session.refresh(obj)
    return obj


async def create_withholding_rule(
    session: AsyncSession,
    *,
    payload: WithholdingTaxRuleCreate,
) -> WithholdingTaxRule:
    obj = WithholdingTaxRule(**payload.model_dump())
    obj.rule_code = obj.rule_code.strip()
    obj.rule_name = obj.rule_name.strip()

    session.add(obj)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise TaxComplianceWorkflowError(
            "Withholding rule already exists"
        ) from exc

    await session.refresh(obj)
    return obj


async def create_tax_period(
    session: AsyncSession,
    *,
    payload: TaxPeriodCreate,
) -> TaxPeriod:
    registration = await get_tax_registration(
        session,
        tenant_id=payload.tenant_id,
        registration_id=payload.registration_id,
    )
    if registration is None:
        raise TaxComplianceWorkflowError(
            "Tax registration not found"
        )

    obj = TaxPeriod(**payload.model_dump())
    obj.period_name = obj.period_name.strip()

    session.add(obj)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise TaxComplianceWorkflowError(
            "Tax period already exists"
        ) from exc

    await session.refresh(obj)
    return obj


async def create_tax_return(
    session: AsyncSession,
    *,
    payload: TaxReturnCreate,
) -> TaxReturn:
    period = await get_tax_period(
        session,
        tenant_id=payload.tenant_id,
        tax_period_id=payload.tax_period_id,
    )
    if period is None:
        raise TaxComplianceWorkflowError(
            "Tax period not found"
        )

    liability = calculate_net_tax_liability(
        output_tax=payload.output_tax,
        input_tax=payload.input_tax,
        adjustments=payload.adjustments,
        credits=payload.credits,
    )

    obj = TaxReturn(
        **payload.model_dump(),
        net_tax_liability=liability,
    )
    obj.return_number = obj.return_number.strip()

    session.add(obj)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise TaxComplianceWorkflowError(
            "Tax return already exists"
        ) from exc

    await session.refresh(obj)
    return obj


async def create_statutory_filing(
    session: AsyncSession,
    *,
    payload: StatutoryFilingCreate,
) -> StatutoryFiling:
    obj = StatutoryFiling(**payload.model_dump())
    obj.filing_number = obj.filing_number.strip()
    obj.filing_type = obj.filing_type.strip()
    obj.notes = obj.notes.strip()

    session.add(obj)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise TaxComplianceWorkflowError(
            "Statutory filing already exists"
        ) from exc

    await session.refresh(obj)
    return obj
