from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.core.enums import FinancialReportStatus
from finance_service.models.financial_reporting import (
    FinancialDisclosureDefinition,
    FinancialReportDefinition,
    FinancialReportLayout,
    FinancialReportLayoutLine,
    FinancialReportRun,
    FinancialReportSnapshot,
)
from finance_service.repositories.financial_reporting import (
    get_report_definition,
    get_report_layout,
    get_report_run,
)
from finance_service.schemas.financial_reporting import (
    FinancialDisclosureDefinitionCreate,
    FinancialReportDefinitionCreate,
    FinancialReportRunCreate,
    FinancialReportSnapshotCreate,
)


class FinancialReportingWorkflowError(ValueError):
    pass


async def create_report_definition(
    session: AsyncSession,
    *,
    payload: FinancialReportDefinitionCreate,
) -> FinancialReportDefinition:
    definition = FinancialReportDefinition(
        tenant_id=payload.tenant_id,
        report_code=payload.report_code.strip(),
        report_name=payload.report_name.strip(),
        report_type=payload.report_type,
        reporting_standard=payload.reporting_standard,
        accounting_basis=payload.accounting_basis,
        default_presentation=payload.default_presentation,
        presentation_currency=(
            payload.presentation_currency.upper()
        ),
        description=payload.description.strip(),
        is_system=payload.is_system,
        created_by=payload.created_by,
    )

    session.add(definition)
    await session.flush()

    for layout_payload in payload.layouts:
        layout = FinancialReportLayout(
            tenant_id=payload.tenant_id,
            definition_id=definition.id,
            layout_code=layout_payload.layout_code.strip(),
            layout_name=layout_payload.layout_name.strip(),
            version_number=layout_payload.version_number,
            is_default=layout_payload.is_default,
            created_by=layout_payload.created_by,
        )

        session.add(layout)
        await session.flush()

        line_ids_by_code = {}

        for line_payload in layout_payload.lines:
            line = FinancialReportLayoutLine(
                tenant_id=payload.tenant_id,
                layout_id=layout.id,
                line_code=line_payload.line_code.strip(),
                line_name=line_payload.line_name.strip(),
                line_type=line_payload.line_type,
                display_order=line_payload.display_order,
                account_filter=line_payload.account_filter,
                formula_expression=(
                    line_payload.formula_expression
                ),
                style_configuration=(
                    line_payload.style_configuration
                ),
                is_visible=line_payload.is_visible,
            )

            session.add(line)
            await session.flush()

            line_ids_by_code[
                line_payload.line_code
            ] = line.id

        for line_payload in layout_payload.lines:
            if line_payload.parent_line_code is None:
                continue

            child = await session.scalar(
                __import__("sqlalchemy").select(
                    FinancialReportLayoutLine
                ).where(
                    FinancialReportLayoutLine.layout_id
                    == layout.id,
                    FinancialReportLayoutLine.line_code
                    == line_payload.line_code,
                )
            )

            if child is not None:
                child.parent_line_id = line_ids_by_code[
                    line_payload.parent_line_code
                ]

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise FinancialReportingWorkflowError(
            "Report definition, layout, or line already exists"
        ) from exc

    await session.refresh(definition)
    return definition


async def create_report_run(
    session: AsyncSession,
    *,
    payload: FinancialReportRunCreate,
) -> FinancialReportRun:
    definition = await get_report_definition(
        session,
        tenant_id=payload.tenant_id,
        definition_id=payload.definition_id,
    )
    layout = await get_report_layout(
        session,
        tenant_id=payload.tenant_id,
        layout_id=payload.layout_id,
    )

    if definition is None:
        raise FinancialReportingWorkflowError(
            "Report definition not found"
        )

    if layout is None:
        raise FinancialReportingWorkflowError(
            "Report layout not found"
        )

    if layout.definition_id != definition.id:
        raise FinancialReportingWorkflowError(
            "Report layout does not belong to definition"
        )

    report_run = FinancialReportRun(
        tenant_id=payload.tenant_id,
        definition_id=payload.definition_id,
        layout_id=payload.layout_id,
        run_number=payload.run_number.strip(),
        period_type=payload.period_type,
        period_start=payload.period_start,
        period_end=payload.period_end,
        comparative_period_start=(
            payload.comparative_period_start
        ),
        comparative_period_end=(
            payload.comparative_period_end
        ),
        presentation=payload.presentation,
        presentation_currency=(
            payload.presentation_currency.upper()
        ),
        consolidation_group_id=(
            payload.consolidation_group_id
        ),
        budget_id=payload.budget_id,
        segment_filter=payload.segment_filter,
        status=FinancialReportStatus.QUEUED,
        requested_by=payload.requested_by,
        parameters=payload.parameters,
    )

    session.add(report_run)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise FinancialReportingWorkflowError(
            "Report run number already exists"
        ) from exc

    await session.refresh(report_run)
    return report_run


async def start_report_run(
    session: AsyncSession,
    *,
    tenant_id,
    run_id,
) -> FinancialReportRun:
    report_run = await get_report_run(
        session,
        tenant_id=tenant_id,
        run_id=run_id,
        for_update=True,
    )

    if report_run is None:
        raise FinancialReportingWorkflowError(
            "Report run not found"
        )

    if report_run.status not in {
        FinancialReportStatus.QUEUED,
        FinancialReportStatus.DRAFT,
    }:
        raise FinancialReportingWorkflowError(
            "Report run cannot be started from current status"
        )

    report_run.status = FinancialReportStatus.RUNNING
    report_run.started_at = datetime.now(timezone.utc)
    report_run.error_message = None

    await session.commit()
    await session.refresh(report_run)

    return report_run


async def complete_report_run(
    session: AsyncSession,
    *,
    tenant_id,
    run_id,
) -> FinancialReportRun:
    report_run = await get_report_run(
        session,
        tenant_id=tenant_id,
        run_id=run_id,
        for_update=True,
    )

    if report_run is None:
        raise FinancialReportingWorkflowError(
            "Report run not found"
        )

    if report_run.status != FinancialReportStatus.RUNNING:
        raise FinancialReportingWorkflowError(
            "Only a running report can be completed"
        )

    report_run.status = FinancialReportStatus.COMPLETED
    report_run.completed_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(report_run)

    return report_run


async def create_report_snapshot(
    session: AsyncSession,
    *,
    payload: FinancialReportSnapshotCreate,
) -> FinancialReportSnapshot:
    report_run = await get_report_run(
        session,
        tenant_id=payload.tenant_id,
        run_id=payload.run_id,
    )

    if report_run is None:
        raise FinancialReportingWorkflowError(
            "Report run not found"
        )

    if report_run.status != FinancialReportStatus.COMPLETED:
        raise FinancialReportingWorkflowError(
            "Snapshot requires a completed report run"
        )

    snapshot = FinancialReportSnapshot(
        tenant_id=payload.tenant_id,
        run_id=payload.run_id,
        snapshot_number=payload.snapshot_number.strip(),
        snapshot_data=payload.snapshot_data,
        document_reference=payload.document_reference,
        content_hash=payload.content_hash,
        generated_by=payload.generated_by,
        is_final=payload.is_final,
    )

    session.add(snapshot)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise FinancialReportingWorkflowError(
            "Snapshot number already exists"
        ) from exc

    await session.refresh(snapshot)
    return snapshot


async def create_disclosure_definition(
    session: AsyncSession,
    *,
    payload: FinancialDisclosureDefinitionCreate,
) -> FinancialDisclosureDefinition:
    disclosure = FinancialDisclosureDefinition(
        tenant_id=payload.tenant_id,
        disclosure_code=payload.disclosure_code.strip(),
        disclosure_name=payload.disclosure_name.strip(),
        reporting_standard=payload.reporting_standard,
        standard_reference=payload.standard_reference,
        description=payload.description.strip(),
        data_requirements=payload.data_requirements,
        is_mandatory=payload.is_mandatory,
    )

    session.add(disclosure)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise FinancialReportingWorkflowError(
            "Disclosure code already exists"
        ) from exc

    await session.refresh(disclosure)
    return disclosure
