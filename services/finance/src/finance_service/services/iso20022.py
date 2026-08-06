from __future__ import annotations

from hashlib import sha256
from xml.etree.ElementTree import (
    Element,
    SubElement,
    tostring,
)

from finance_service.models.banking import BankAccount
from finance_service.models.treasury import (
    TreasuryPaymentBatch,
    TreasuryPaymentItem,
)


class Iso20022GenerationError(ValueError):
    pass


def _text(parent, tag: str, value: str):
    node = SubElement(parent, tag)
    node.text = value
    return node


def generate_pain001_xml(
    *,
    batch: TreasuryPaymentBatch,
    bank_account: BankAccount,
    items: list[TreasuryPaymentItem],
) -> tuple[str, str]:
    if not items:
        raise Iso20022GenerationError(
            "Payment batch contains no items"
        )

    document = Element(
        "Document",
        {
            "xmlns": (
                "urn:iso:std:iso:20022:tech:xsd:"
                "pain.001.001.03"
            )
        },
    )

    initiation = SubElement(
        document,
        "CstmrCdtTrfInitn",
    )

    group_header = SubElement(initiation, "GrpHdr")
    _text(group_header, "MsgId", str(batch.id))
    _text(
        group_header,
        "CreDtTm",
        batch.created_at.isoformat(),
    )
    _text(group_header, "NbOfTxs", str(len(items)))
    _text(group_header, "CtrlSum", str(batch.total_amount))

    initiating_party = SubElement(
        group_header,
        "InitgPty",
    )
    _text(
        initiating_party,
        "Nm",
        bank_account.account_name,
    )

    payment_info = SubElement(initiation, "PmtInf")
    _text(payment_info, "PmtInfId", batch.batch_number)
    _text(payment_info, "PmtMtd", "TRF")
    _text(payment_info, "BtchBookg", "true")
    _text(payment_info, "NbOfTxs", str(len(items)))
    _text(payment_info, "CtrlSum", str(batch.total_amount))
    _text(
        payment_info,
        "ReqdExctnDt",
        batch.execution_date.isoformat(),
    )

    debtor = SubElement(payment_info, "Dbtr")
    _text(debtor, "Nm", bank_account.account_name)

    debtor_account = SubElement(payment_info, "DbtrAcct")
    debtor_account_id = SubElement(debtor_account, "Id")

    if bank_account.iban:
        _text(
            debtor_account_id,
            "IBAN",
            bank_account.iban,
        )
    else:
        other = SubElement(debtor_account_id, "Othr")
        _text(other, "Id", bank_account.account_number)

    debtor_agent = SubElement(payment_info, "DbtrAgt")
    financial = SubElement(
        debtor_agent,
        "FinInstnId",
    )

    if bank_account.swift_code:
        _text(
            financial,
            "BIC",
            bank_account.swift_code,
        )
    else:
        _text(financial, "Nm", bank_account.bank_name)

    for item in items:
        transfer = SubElement(
            payment_info,
            "CdtTrfTxInf",
        )

        payment_id = SubElement(transfer, "PmtId")
        _text(
            payment_id,
            "EndToEndId",
            item.payment_reference,
        )

        amount = SubElement(transfer, "Amt")
        instructed = SubElement(
            amount,
            "InstdAmt",
            {"Ccy": item.currency_code},
        )
        instructed.text = str(item.amount)

        creditor = SubElement(transfer, "Cdtr")
        _text(
            creditor,
            "Nm",
            item.beneficiary_name,
        )

        creditor_account = SubElement(
            transfer,
            "CdtrAcct",
        )
        creditor_account_id = SubElement(
            creditor_account,
            "Id",
        )

        if item.beneficiary_iban:
            _text(
                creditor_account_id,
                "IBAN",
                item.beneficiary_iban,
            )
        else:
            other = SubElement(
                creditor_account_id,
                "Othr",
            )
            _text(
                other,
                "Id",
                item.beneficiary_account,
            )

        remittance = SubElement(transfer, "RmtInf")
        _text(
            remittance,
            "Ustrd",
            item.payment_reference,
        )

    xml_bytes = tostring(
        document,
        encoding="utf-8",
        xml_declaration=True,
    )

    content = xml_bytes.decode("utf-8")
    digest = sha256(xml_bytes).hexdigest()

    return content, digest
