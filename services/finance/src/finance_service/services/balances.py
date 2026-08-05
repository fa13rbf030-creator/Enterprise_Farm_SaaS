from __future__ import annotations

from decimal import Decimal

from finance_service.core.enums import (
    BalanceDirection,
    NormalBalance,
)


def calculate_net_balance(
    *,
    debit: Decimal,
    credit: Decimal,
    normal_balance: NormalBalance,
) -> tuple[Decimal, Decimal]:
    if normal_balance == NormalBalance.DEBIT:
        net = debit - credit

        if net >= 0:
            return net, Decimal("0")

        return Decimal("0"), abs(net)

    net = credit - debit

    if net >= 0:
        return Decimal("0"), net

    return abs(net), Decimal("0")


def determine_balance_direction(
    *,
    debit: Decimal,
    credit: Decimal,
) -> BalanceDirection:
    if debit > credit:
        return BalanceDirection.DEBIT

    if credit > debit:
        return BalanceDirection.CREDIT

    return BalanceDirection.ZERO
