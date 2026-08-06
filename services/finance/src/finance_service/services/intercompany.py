from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.models.intercompany import (
    ConsolidationGroup,
    ConsolidationGroupMember,
    ConsolidationPeriod,
    IntercompanyAccountMapping,
    IntercompanyOrganization,
    IntercompanyRelationship,
    IntercompanyTransaction,
)
from finance_service.repositories.intercompany import (
    get_consolidation_group,
    get_intercompany_organization,
)
from finance_service.schemas.intercompany import (
    ConsolidationGroupCreate,
    ConsolidationPeriodCreate,
    IntercompanyAccountMappingCreate,
    IntercompanyOrganizationCreate,
    IntercompanyRelationshipCreate,
    IntercompanyTransactionCreate,
)
from finance_service.services.intercompany_calculations import (
    calculate_base_amount,
)


class IntercompanyWorkflowError(ValueError):
    pass


async def create_intercompany_organization(
    session: AsyncSession,
    *,
    payload: IntercompanyOrganizationCreate,
) -> IntercompanyOrganization:
    organization = IntercompanyOrganization(
        tenant_id=payload.tenant_id,
        organization_code=payload.organization_code.strip(),
        organization_name=payload.organization_name.strip(),
        base_currency=payload.base_currency.upper(),
    )

    session.add(organization)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise IntercompanyWorkflowError(
            "Organization code already exists"
        ) from exc

    await session.refresh(organization)
    return organization


async def create_intercompany_relationship(
    session: AsyncSession,
    *,
    payload: IntercompanyRelationshipCreate,
) -> IntercompanyRelationship:
    parent = await get_intercompany_organization(
        session,
        tenant_id=payload.tenant_id,
        organization_id=payload.parent_company_id,
    )
    child = await get_intercompany_organization(
        session,
        tenant_id=payload.tenant_id,
        organization_id=payload.child_company_id,
    )

    if parent is None or child is None:
        raise IntercompanyWorkflowError(
            "Parent or child organization not found"
        )

    relationship = IntercompanyRelationship(
        tenant_id=payload.tenant_id,
        parent_company_id=payload.parent_company_id,
        child_company_id=payload.child_company_id,
        relationship_type=payload.relationship_type,
        ownership_percentage=payload.ownership_percentage,
        voting_percentage=payload.voting_percentage,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
    )

    session.add(relationship)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise IntercompanyWorkflowError(
            "Intercompany relationship already exists"
        ) from exc

    await session.refresh(relationship)
    return relationship


async def create_intercompany_account_mapping(
    session: AsyncSession,
    *,
    payload: IntercompanyAccountMappingCreate,
) -> IntercompanyAccountMapping:
    source = await get_intercompany_organization(
        session,
        tenant_id=payload.tenant_id,
        organization_id=payload.source_organization_id,
    )
    destination = await get_intercompany_organization(
        session,
        tenant_id=payload.tenant_id,
        organization_id=payload.destination_organization_id,
    )

    if source is None or destination is None:
        raise IntercompanyWorkflowError(
            "Mapping organization not found"
        )

    mapping = IntercompanyAccountMapping(
        tenant_id=payload.tenant_id,
        source_organization_id=payload.source_organization_id,
        destination_organization_id=(
            payload.destination_organization_id
        ),
        source_due_from_account_id=(
            payload.source_due_from_account_id
        ),
        source_due_to_account_id=payload.source_due_to_account_id,
        destination_due_from_account_id=(
            payload.destination_due_from_account_id
        ),
        destination_due_to_account_id=(
            payload.destination_due_to_account_id
        ),
        settlement_currency=payload.settlement_currency.upper(),
    )

    session.add(mapping)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise IntercompanyWorkflowError(
            "Intercompany account mapping already exists"
        ) from exc

    await session.refresh(mapping)
    return mapping


async def create_consolidation_group(
    session: AsyncSession,
    *,
    payload: ConsolidationGroupCreate,
) -> ConsolidationGroup:
    parent = await get_intercompany_organization(
        session,
        tenant_id=payload.tenant_id,
        organization_id=payload.parent_organization_id,
    )

    if parent is None:
        raise IntercompanyWorkflowError(
            "Parent organization not found"
        )

    group = ConsolidationGroup(
        tenant_id=payload.tenant_id,
        group_code=payload.group_code.strip(),
        group_name=payload.group_name.strip(),
        parent_organization_id=payload.parent_organization_id,
        presentation_currency=(
            payload.presentation_currency.upper()
        ),
        description=payload.description.strip(),
        created_by=payload.created_by,
    )

    session.add(group)
    await session.flush()

    for member_payload in payload.members:
        organization = await get_intercompany_organization(
            session,
            tenant_id=payload.tenant_id,
            organization_id=member_payload.organization_id,
        )

        if organization is None:
            raise IntercompanyWorkflowError(
                "Consolidation member organization not found"
            )

        session.add(
            ConsolidationGroupMember(
                tenant_id=payload.tenant_id,
                group_id=group.id,
                organization_id=member_payload.organization_id,
                consolidation_method=(
                    member_payload.consolidation_method
                ),
                ownership_percentage=(
                    member_payload.ownership_percentage
                ),
                voting_percentage=(
                    member_payload.voting_percentage
                ),
                effective_from=member_payload.effective_from,
                effective_to=member_payload.effective_to,
            )
        )

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise IntercompanyWorkflowError(
            "Consolidation group or member already exists"
        ) from exc

    await session.refresh(group)
    return group


async def create_consolidation_period(
    session: AsyncSession,
    *,
    payload: ConsolidationPeriodCreate,
) -> ConsolidationPeriod:
    group = await get_consolidation_group(
        session,
        tenant_id=payload.tenant_id,
        group_id=payload.group_id,
    )

    if group is None:
        raise IntercompanyWorkflowError(
            "Consolidation group not found"
        )

    period = ConsolidationPeriod(
        tenant_id=payload.tenant_id,
        group_id=payload.group_id,
        period_name=payload.period_name.strip(),
        period_start=payload.period_start,
        period_end=payload.period_end,
        presentation_currency=(
            payload.presentation_currency.upper()
        ),
        opened_by=payload.opened_by,
    )

    session.add(period)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise IntercompanyWorkflowError(
            "Consolidation period already exists"
        ) from exc

    await session.refresh(period)
    return period


async def create_intercompany_transaction(
    session: AsyncSession,
    *,
    payload: IntercompanyTransactionCreate,
) -> IntercompanyTransaction:
    source = await get_intercompany_organization(
        session,
        tenant_id=payload.tenant_id,
        organization_id=payload.source_organization_id,
    )
    destination = await get_intercompany_organization(
        session,
        tenant_id=payload.tenant_id,
        organization_id=payload.destination_organization_id,
    )

    if source is None or destination is None:
        raise IntercompanyWorkflowError(
            "Transaction organization not found"
        )

    base_amount = calculate_base_amount(
        transaction_amount=payload.amount,
        exchange_rate=payload.exchange_rate,
    )

    transaction = IntercompanyTransaction(
        tenant_id=payload.tenant_id,
        transaction_number=payload.transaction_number.strip(),
        source_organization_id=payload.source_organization_id,
        destination_organization_id=(
            payload.destination_organization_id
        ),
        transaction_date=payload.transaction_date,
        due_date=payload.due_date,
        currency_code=payload.currency_code.upper(),
        amount=payload.amount,
        exchange_rate=payload.exchange_rate,
        base_amount=base_amount,
        source_reference=payload.source_reference,
        destination_reference=payload.destination_reference,
        created_by=payload.created_by,
    )

    session.add(transaction)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise IntercompanyWorkflowError(
            "Intercompany transaction number already exists"
        ) from exc

    await session.refresh(transaction)
    return transaction
