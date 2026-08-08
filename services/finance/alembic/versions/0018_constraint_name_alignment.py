"""align finance check constraint names with stable metadata names

Revision ID: 0018_constraint_name_alignment
Revises: 0017_finance_analytics
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0018_constraint_name_alignment"
down_revision: Union[str, Sequence[str], None] = "0017_finance_analytics"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


RENAMES = (
    (
        "finance_close_task_dependencies",
        "ck_finance_close_task_dependencies_ck_finance_close_tas_5868",
        "ck_finance_close_task_dependencies_no_self_dependency",
    ),
    (
        "finance_consolidation_group_members",
        "ck_finance_consolidation_group_members_ck_consolidation_0819",
        "ck_finance_consolidation_group_members_ownership_pct",
    ),
    (
        "finance_consolidation_group_members",
        "ck_finance_consolidation_group_members_ck_consolidation_7255",
        "ck_finance_consolidation_group_members_voting_pct",
    ),
    (
        "finance_consolidation_periods",
        "ck_finance_consolidation_periods_ck_consolidation_perio_9efd",
        "ck_finance_consolidation_periods_valid_range",
    ),
    (
        "finance_intercompany_account_mappings",
        "ck_finance_intercompany_account_mappings_ck_ic_account__30fc",
        "ck_finance_intercompany_account_mappings_distinct_orgs",
    ),
    (
        "finance_intercompany_transactions",
        "ck_finance_intercompany_transactions_ck_intercompany_tr_42db",
        "ck_finance_intercompany_transactions_positive_amount",
    ),
    (
        "finance_intercompany_transactions",
        "ck_finance_intercompany_transactions_ck_intercompany_tr_44a1",
        "ck_finance_intercompany_transactions_distinct_orgs",
    ),
    (
        "finance_livestock_zakat_rules",
        "ck_finance_livestock_zakat_rules_ck_finance_livestock_z_c87e",
        "ck_finance_livestock_zakat_rules_count_range",
    ),
    (
        "finance_report_layout_lines",
        "ck_finance_report_layout_lines_ck_finance_report_layout_9636",
        "ck_finance_report_layout_lines_display_order",
    ),
)


def _rename_constraint(
    table_name: str,
    old_name: str,
    new_name: str,
) -> None:
    op.execute(
        f'ALTER TABLE "{table_name}" '
        f'RENAME CONSTRAINT "{old_name}" TO "{new_name}"'
    )


def upgrade() -> None:
    for table_name, old_name, new_name in RENAMES:
        _rename_constraint(
            table_name,
            old_name,
            new_name,
        )


def downgrade() -> None:
    for table_name, old_name, new_name in reversed(RENAMES):
        _rename_constraint(
            table_name,
            new_name,
            old_name,
        )
