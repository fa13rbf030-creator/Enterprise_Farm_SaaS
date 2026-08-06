from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.core.enums import (
    FinancialCloseExceptionStatus,
    FinancialCloseStatus,
    FinancialCloseTaskStatus,
)
from finance_service.models.financial_close import (
    FinancialCloseCycle,
    FinancialCloseException,
    FinancialCloseSignOff,
    FinancialCloseTask,
    FinancialPeriodLock,
)
from finance_service.repositories.financial_close import (
    get_active_period_lock,
    get_close_cycle,
    get_close_task,
)
from finance_service.schemas.financial_close import (
    FinancialCloseCycleCreate,
    FinancialCloseExceptionCreate,
    FinancialCloseSignOffCreate,
    FinancialCloseTaskStatusUpdate,
    FinancialPeriodLockCreate,
    FinancialPeriodUnlock,
)
from finance_service.services.financial_close_calculations import (
    is_exception_material,
)


class FinancialCloseWorkflowError(ValueError):
    pass


async def create_close_cycle(
    session: AsyncSession,
    *,
    payload: FinancialCloseCycleCreate,
) -> FinancialCloseCycle:
    cycle = FinancialCloseCycle(
        tenant_id=payload.tenant_id,
        cycle_code=payload.cycle_code.strip(),
        cycle_name=payload.cycle_name.strip(),
        cycle_type=payload.cycle_type,
        period_start=payload.period_start,
        period_end=payload.period_end,
        fiscal_period_id=payload.fiscal_period_id,
        consolidation_period_id=payload.consolidation_period_id,
        materiality_threshold=payload.materiality_threshold,
        planned_close_date=payload.planned_close_date,
        opened_by=payload.opened_by,
        description=payload.description.strip(),
    )

    session.add(cycle)
    await session.flush()

    for task_payload in payload.tasks:
        session.add(
            FinancialCloseTask(
                tenant_id=payload.tenant_id,
                cycle_id=cycle.id,
                task_code=task_payload.task_code.strip(),
                task_name=task_payload.task_name.strip(),
                task_type=task_payload.task_type,
                owner_id=task_payload.owner_id,
                reviewer_id=task_payload.reviewer_id,
                due_date=task_payload.due_date,
                evidence_reference=(
                    task_payload.evidence_reference
                ),
                notes=task_payload.notes.strip(),
                is_mandatory=task_payload.is_mandatory,
            )
        )

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise FinancialCloseWorkflowError(
            "Close cycle or task code already exists"
        ) from exc

    await session.refresh(cycle)
    return cycle


async def update_close_task_status(
    session: AsyncSession,
    *,
    task_id: UUID,
    payload: FinancialCloseTaskStatusUpdate,
) -> FinancialCloseTask:
    task = await get_close_task(
        session,
        tenant_id=payload.tenant_id,
        task_id=task_id,
        for_update=True,
    )

    if task is None:
        raise FinancialCloseWorkflowError(
            "Close task not found"
        )

    now = datetime.now(timezone.utc)

    if payload.status == FinancialCloseTaskStatus.IN_PROGRESS:
        task.started_at = task.started_at or now

    if payload.status == FinancialCloseTaskStatus.SUBMITTED:
        task.completed_at = now

    if payload.status == FinancialCloseTaskStatus.APPROVED:
        task.approved_at = now

    task.status = payload.status
    task.evidence_reference = (
        payload.evidence_reference
        or task.evidence_reference
    )

    if payload.notes:
        task.notes = payload.notes.strip()

    await session.commit()
    await session.refresh(task)

    return task


async def create_close_exception(
    session: AsyncSession,
    *,
    payload: FinancialCloseExceptionCreate,
) -> FinancialCloseException:
    cycle = await get_close_cycle(
        session,
        tenant_id=payload.tenant_id,
        cycle_id=payload.cycle_id,
    )

    if cycle is None:
        raise FinancialCloseWorkflowError(
            "Close cycle not found"
        )

    exception = FinancialCloseException(
        tenant_id=payload.tenant_id,
        cycle_id=payload.cycle_id,
        task_id=payload.task_id,
        exception_number=payload.exception_number.strip(),
        title=payload.title.strip(),
        description=payload.description.strip(),
        severity=payload.severity,
        status=FinancialCloseExceptionStatus.OPEN,
        amount=payload.amount,
        is_material=is_exception_material(
            exception_amount=payload.amount,
            materiality_threshold=cycle.materiality_threshold,
        ),
        assigned_to=payload.assigned_to,
    )

    session.add(exception)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise FinancialCloseWorkflowError(
            "Close exception number already exists"
        ) from exc

    await session.refresh(exception)
    return exception


async def sign_off_close_cycle(
    session: AsyncSession,
    *,
    payload: FinancialCloseSignOffCreate,
) -> FinancialCloseSignOff:
    cycle = await get_close_cycle(
        session,
        tenant_id=payload.tenant_id,
        cycle_id=payload.cycle_id,
    )

    if cycle is None:
        raise FinancialCloseWorkflowError(
            "Close cycle not found"
        )

    signoff = FinancialCloseSignOff(
        tenant_id=payload.tenant_id,
        cycle_id=payload.cycle_id,
        role=payload.role,
        signer_id=payload.signer_id,
        comments=payload.comments.strip(),
    )

    session.add(signoff)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise FinancialCloseWorkflowError(
            "Sign-off role already completed"
        ) from exc

    await session.refresh(signoff)
    return signoff


async def lock_financial_period(
    session: AsyncSession,
    *,
    payload: FinancialPeriodLockCreate,
) -> FinancialPeriodLock:
    existing = await get_active_period_lock(
        session,
        tenant_id=payload.tenant_id,
        fiscal_period_id=payload.fiscal_period_id,
    )

    if existing is not None:
        raise FinancialCloseWorkflowError(
            "Fiscal period is already locked"
        )

    period_lock = FinancialPeriodLock(
        tenant_id=payload.tenant_id,
        fiscal_period_id=payload.fiscal_period_id,
        cycle_id=payload.cycle_id,
        lock_type=payload.lock_type,
        locked_by=payload.locked_by,
        reason=payload.reason.strip(),
    )

    session.add(period_lock)
    await session.commit()
    await session.refresh(period_lock)

    return period_lock


async def unlock_financial_period(
    session: AsyncSession,
    *,
    lock_id: UUID,
    payload: FinancialPeriodUnlock,
) -> FinancialPeriodLock:
    lock = await session.get(
        FinancialPeriodLock,
        lock_id,
        with_for_update=True,
    )

    if lock is None or lock.tenant_id != payload.tenant_id:
        raise FinancialCloseWorkflowError(
            "Period lock not found"
        )

    if not lock.is_active:
        raise FinancialCloseWorkflowError(
            "Period lock is already inactive"
        )

    lock.is_active = False
    lock.unlocked_by = payload.unlocked_by
    lock.unlocked_at = datetime.now(timezone.utc)

    if payload.reason:
        lock.reason = payload.reason.strip()

    await session.commit()
    await session.refresh(lock)

    return lock


async def open_close_cycle(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    cycle_id: UUID,
) -> FinancialCloseCycle:
    cycle = await get_close_cycle(
        session,
        tenant_id=tenant_id,
        cycle_id=cycle_id,
        for_update=True,
    )

    if cycle is None:
        raise FinancialCloseWorkflowError(
            "Close cycle not found"
        )

    if cycle.status not in {
        FinancialCloseStatus.DRAFT,
        FinancialCloseStatus.REOPENED,
    }:
        raise FinancialCloseWorkflowError(
            "Close cycle cannot be opened from current status"
        )

    cycle.status = FinancialCloseStatus.OPEN

    await session.commit()
    await session.refresh(cycle)

    return cycle
