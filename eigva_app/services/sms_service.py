from decimal import Decimal, ROUND_DOWN
from eigva_app.models.sms_transaction import SmsTransaction
from sqlalchemy import func
from eigva_app.config import SMS_PRICE_PER_SMS

def topup_sms(db, buyer_id: int, amount_eur: Decimal):
    price_per_sms = SMS_PRICE_PER_SMS

    sms_count = int((amount_eur / price_per_sms).quantize(Decimal("1"), rounding=ROUND_DOWN))

    tx = SmsTransaction(
        buyer_id=buyer_id,
        type="credit",
        reason="topup",
        amount_eur=amount_eur,
        sms_count=sms_count,
        price_per_sms=price_per_sms,
        invoiced=False
    )

    db.add(tx)
    db.commit()
    db.refresh(tx)

    return tx


def get_sms_balance_eur(db, buyer_id: int) -> Decimal:
    credit = db.query(
        func.coalesce(func.sum(SmsTransaction.amount_eur), 0)
    ).filter(
        SmsTransaction.buyer_id == buyer_id,
        SmsTransaction.type == "credit"
    ).scalar()

    debit = db.query(
        func.coalesce(func.sum(SmsTransaction.amount_eur), 0)
    ).filter(
        SmsTransaction.buyer_id == buyer_id,
        SmsTransaction.type == "debit"
    ).scalar()

    return Decimal(credit or 0) - Decimal(debit or 0)


def get_sms_balance_count(db, buyer_id: int) -> int:
    credit = db.query(
        func.coalesce(func.sum(SmsTransaction.sms_count), 0)
    ).filter(
        SmsTransaction.buyer_id == buyer_id,
        SmsTransaction.type == "credit"
    ).scalar()

    debit = db.query(
        func.coalesce(func.sum(SmsTransaction.sms_count), 0)
    ).filter(
        SmsTransaction.buyer_id == buyer_id,
        SmsTransaction.type == "debit"
    ).scalar()

    return (credit or 0) - (debit or 0)