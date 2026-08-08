from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.models.finance_controls import (
    AttestationStatus,
    FinanceAuditEvidence,
    FinanceControlAttestation,
    FinanceControlDefinition,
    FinanceControlException,
    FinanceControlExecution,
    FinanceControlExecutionStatus,
    FinanceReconciliationRun,
    ReconciliationStatus,
)
from finance_service.repositories.finance_controls import (
    get_control_definition,
)
from finance_service.schemas.finance_controls import (
    FinanceAuditEvidenceCreate,
    FinanceControlAttestationCreate,
    FinanceControlDefinitionCreate,
    FinanceControlExceptionCreate,
    FinanceControlExecutionCreate,
    FinanceReconciliationRunCreate,
)
from finance_service.services.finance_control_calculations import (
    calculate_control_effectiveness,
    calculate_reconciliation_variance,
    calculate_residual_risk_score,
    is_reconciliation_within_tolerance,
)


class FinanceControlWorkflowError(ValueError):
    pass


async def create_control_definition(
    session: AsyncSession,
    *,
    payload: FinanceControlDefinitionCreate,
) -> FinanceControlDefinition:
    obj = FinanceControlDefinition(
        **payload.model_dump()
    )
    obj.control_code = obj.control_code.strip()
    obj.control_name = obj.control_name.strip()
    obj.module_name = obj.module_name.strip()

    session.add(obj)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise FinanceControlWorkflowError(
            "Finance control code already exists"
        ) from exc

    await session.refresh(obj)
    return obj


async def create_control_execution(
    session: AsyncSession,
    *,
    payload: FinanceControlExecutionCreate,
) -> FinanceControlExecution:
    control = await get_control_definition(
        session,
        tenant_id=payload.tenant_id,
        control_id=payload.control_id,
    )

    if control is None:
        raise FinanceControlWorkflowError(
            "Finance control definition not found"
        )

    effectiveness = calculate_control_effectiveness(
        passed_checks=payload.passed_checks,
        total_checks=payload.tested_population,
    )

    residual = calculate_residual_risk_score(
        inherent_risk_score=control.inherent_risk_score,
        control_effectiveness_percentage=effectiveness,
    )

    status = (
        FinanceControlExecutionStatus.PASSED
        if payload.failed_checks == 0
        else FinanceControlExecutionStatus.EXCEPTION
    )

    obj = FinanceControlExecution(
        **payload.model_dump(),
        effectiveness_percentage=effectiveness,
        residual_risk_score=residual,
        status=status,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )

    session.add(obj)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise FinanceControlWorkflowError(
            "Control execution number already exists"
        ) from exc

    await session.refresh(obj)
    return obj


async def create_reconciliation_run(
    session: AsyncSession,
    *,
    payload: FinanceReconciliationRunCreate,
) -> FinanceReconciliationRun:
    variance = calculate_reconciliation_variance(
        source_balance=payload.source_balance,
        target_balance=payload.target_balance,
    )

    matched = is_reconciliation_within_tolerance(
        source_balance=payload.source_balance,
        target_balance=payload.target_balance,
        tolerance=payload.tolerance,
    )

    obj = FinanceReconciliationRun(
        **payload.model_dump(),
        variance=variance,
        status=(
            ReconciliationStatus.MATCHED
            if matched
            else ReconciliationStatus.UNMATCHED
        ),
        completed_at=datetime.now(timezone.utc),
    )

    session.add(obj)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise FinanceControlWorkflowError(
            "Reconciliation number already exists"
        ) from exc

    await session.refresh(obj)
    return obj


async def create_control_exception(
    session: AsyncSession,
    *,
    payload: FinanceControlExceptionCreate,
) -> FinanceControlException:
    obj = FinanceControlException(
        **payload.model_dump()
    )
    obj.exception_number = obj.exception_number.strip()
    obj.title = obj.title.strip()
    obj.description = obj.description.strip()

    session.add(obj)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise FinanceControlWorkflowError(
            "Control exception number already exists"
        ) from exc

    await session.refresh(obj)
    return obj


async def create_control_attestation(
    session: AsyncSession,
    *,
    payload: FinanceControlAttestationCreate,
) -> FinanceControlAttestation:
    control = await get_control_definition(
        session,
        tenant_id=payload.tenant_id,
        control_id=payload.control_id,
    )

    if control is None:
        raise FinanceControlWorkflowError(
            "Finance control definition not found"
        )

    obj = FinanceControlAttestation(
        **payload.model_dump(),
        status=AttestationStatus.ATTESTED,
        attested_at=datetime.now(timezone.utc),
    )

    session.add(obj)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise FinanceControlWorkflowError(
            "Control attestation number already exists"
        ) from exc

    await session.refresh(obj)
    return obj


async def create_audit_evidence(
    session: AsyncSession,
    *,
    payload: FinanceAuditEvidenceCreate,
) -> FinanceAuditEvidence:
    obj = FinanceAuditEvidence(
        **payload.model_dump()
    )
    obj.evidence_number = obj.evidence_number.strip()
    obj.evidence_type = obj.evidence_type.strip()
    obj.notes = obj.notes.strip()

    session.add(obj)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise FinanceControlWorkflowError(
            "Audit evidence number already exists"
        ) from exc

    await session.refresh(obj)
    return obj
