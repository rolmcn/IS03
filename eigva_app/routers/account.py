import logging
from typing import Annotated

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from eigva_app.database import get_async_session
from eigva_app.models import Buyer, User
from eigva_app.schemas.buyer_schemas import buyerSchema
from eigva_app.core.security.crypto import encrypt_data, hash_full_name_email, hash_identification_code, hash_vat_code
from eigva_app.services.account_service import get_user_messages, mark_message_read
from eigva_app.utils.choices_municipalities import MUNICIPALITIES
from eigva_app.core.security.auth import get_current_user, get_current_buyer
from eigva_app.config import templates

logger = logging.getLogger(__name__)
router = APIRouter()

# ---------------------
# Depends tipai
# ---------------------
CurrentUser = Annotated[User, Depends(get_current_user)]
Currentbuyer = Annotated[Buyer, Depends(get_current_buyer)]
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]


# ---------------- GET ACCOUNT PAGE ----------------
@router.get("/account", response_class=HTMLResponse)
async def account_page(
    request: Request,
    current_user: CurrentUser,
    current_buyer: Currentbuyer,
    session: SessionDep,
):

    messages = await get_user_messages(session, current_user.id)
    success_message = request.query_params.get("success")
    error_message = request.query_params.get("error")
    active_tab = request.query_params.get("active_tab")

    scenario = None
    if current_buyer.status == "pending":
        scenario = "pending"
    elif current_buyer.status == "active":
        scenario = "active"

    return templates.TemplateResponse(
        "account.html",
        {
            "request": request,
            "current_user": {
                "first_name": current_user.first_name,
                "last_name": current_user.last_name,
                "mobile_phone": current_user.mobile_phone,
                "email": current_user.email,
                "super_user": current_user.super_user,
                "email_verified_at": current_user.email_verified_at,
            },
            "current_buyer": {
                "buyer_type": current_buyer.buyer_type,
                "full_name": current_buyer.full_name,
                "identification_code": current_buyer.identification_code,
                "vat_status": current_buyer.vat_status,
                "vat_code": current_buyer.vat_code,
                "street": current_buyer.street,
                "house_number": current_buyer.house_number,
                "apartment_number": current_buyer.apartment_number,
                "postal_code": current_buyer.postal_code,
                "settlement": current_buyer.settlement,
                "municipality": current_buyer.municipality,
                "country": current_buyer.country,
                "mobile_phone": current_buyer.mobile_phone,
                "email": current_buyer.email,
            },
            "active_page": "account",
            "environment": "auto",
            "messages": messages,
            "success_message": success_message,
            "error_message": error_message,
            "active_tab": active_tab,

            "MUNICIPALITIES": MUNICIPALITIES,
            "scenario": scenario
        },
    )

# ---------------- MARK MESSAGE READ ----------------
@router.post("/account/mark_read/{msg_id}")
async def mark_message_read_route(
    msg_id: int,
    current_user: CurrentUser,
    session: SessionDep,
):
    message = await mark_message_read(session, current_user.id, msg_id)

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    return JSONResponse({
        "status": "ok",
        "msg_read": message.msg_read.isoformat() if message.msg_read else None
    })


# ---------------- SAVE buyer ----------------
@router.post("/account/save_buyer")
async def save_buyer(
    request: Request,
    session: SessionDep,
    current_buyer: Currentbuyer
):
    data = await request.form()
    form_data = dict(data)
    field_errors = {}

    # -----------------------------
    # 1. Pydantic validacija
    # -----------------------------
    try:
        buyer_schema = buyerSchema(**form_data)
    except ValidationError as e:
        for err in e.errors():
            loc = err.get("loc", [])
            msg = err.get("msg", "")
            if msg:
                msg = msg.replace("Value error, ", "")
            if loc:
                field_errors[loc[-1]] = msg

        scenario = "pydantic"
        return JSONResponse({
            "form_data": form_data,
            "field_errors": field_errors,
            "scenario": scenario
        })

    # -----------------------------
    # 2. Unikalumo tikrinimas
    # -----------------------------
    duplicates = {}
    full_name_email_hash_val = None
    ident_hash_val = None
    vat_hash_val = None

    scenario = "unique"

    if buyer_schema.buyer_type == "physical":
        full_name_email_hash_val = hash_full_name_email(
            buyer_schema.full_name, buyer_schema.email
        )
        result = await session.execute(
            select(Buyer).where(
                Buyer.full_name_email_hash == full_name_email_hash_val,
                            Buyer.id != current_buyer.id
            )
        )
        if result.scalars().first():
            duplicates["email"] = "Mokėtojas su tokiu el. pašto adresu jau egzistuoja"

    if buyer_schema.buyer_type == "legal" and buyer_schema.identification_code:
        ident_hash_val = hash_identification_code(buyer_schema.identification_code)
        result = await session.execute(
            select(Buyer).where(
                Buyer.identification_code_hash == ident_hash_val,
                Buyer.id != current_buyer.id
            )
        )
        if result.scalars().first():
            duplicates["identification_code"] = (
                "Toks mokėtojas jau egzistuoja. Patikrinkite ar teisingai nurodytas įmonės kodas."
            )

    if buyer_schema.vat_status == "yes" and buyer_schema.vat_code:
        vat_hash_val = hash_vat_code(buyer_schema.vat_code)
        result = await session.execute(
            select(Buyer).where(
                Buyer.vat_code_hash == vat_hash_val,
                Buyer.id != current_buyer.id
            )
        )
        if result.scalars().first():
            duplicates["vat_code"] = (
                "Toks mokėtojas jau egzistuoja. Patikrinkite ar teisingai nurodytas PVM kodas."
            )

    if duplicates:
        return JSONResponse({
            "form_data": form_data,
            "field_errors": duplicates,
            "scenario": scenario
        })

    # -----------------------------
    # 3. Šifravimas
    # -----------------------------
    buyer_data = {
        "buyer_type": buyer_schema.buyer_type,
        "vat_status": buyer_schema.vat_status,
        "municipality": buyer_schema.municipality,
        "full_name_encrypted": encrypt_data(buyer_schema.full_name),
        "identification_code_encrypted": encrypt_data(buyer_schema.identification_code) if buyer_schema.identification_code else None,
        "vat_code_encrypted": encrypt_data(buyer_schema.vat_code) if buyer_schema.vat_code else None,
        "street_encrypted": encrypt_data(buyer_schema.street),
        "house_number_encrypted": encrypt_data(buyer_schema.house_number),
        "apartment_number_encrypted": encrypt_data(buyer_schema.apartment_number) if buyer_schema.apartment_number else None,
        "postal_code_encrypted": encrypt_data(buyer_schema.postal_code),
        "settlement_encrypted": encrypt_data(buyer_schema.settlement),
        "mobile_phone_encrypted": encrypt_data(buyer_schema.mobile_phone) if buyer_schema.mobile_phone else None,
        "email_encrypted": encrypt_data(buyer_schema.email),
        "full_name_email_hash": full_name_email_hash_val,
        "identification_code_hash": ident_hash_val,
        "vat_code_hash": vat_hash_val,
        "status": "active",
    }

    # -----------------------------
    # 4. Įrašymas į DB
    # -----------------------------
    try:
        buyer = current_buyer
        for key, value in buyer_data.items():
            # Tikriname, ar objektas turi property su setteriu
            prop = getattr(type(buyer), key, None)
            if isinstance(prop, property) and prop.fset:
                setattr(buyer, key, value)  # property su setteriu
            elif hasattr(buyer, key):
                setattr(buyer, key, value)  # tiesiog column (_encrypted ar kiti)
            # jei nėra column ir nėra setterio – ignoruojame
        await session.commit()
        await session.refresh(buyer)
    except IntegrityError as e:
        await session.rollback()
        logger.error(f"DB integrity error: {e}")
        scenario = "saving-error"
        return JSONResponse({"scenario": scenario})
    except Exception as e:
        await session.rollback()
        logger.exception(f"Unexpected error while saving buyer: {e}")
        scenario = "server-error"
        return JSONResponse({"scenario": scenario})

    # -----------------------------
    # 5. Sėkmės pranešimas
    # -----------------------------
    scenario = "success"
    return JSONResponse({
        "scenario": scenario,
        "buyer": {
            "buyer_type": buyer.buyer_type,
            "full_name": buyer.full_name,
            "identification_code": buyer.identification_code,
            "vat_code": buyer.vat_code,
            "street": buyer.street,
            "house_number": buyer.house_number,
            "apartment_number": buyer.apartment_number,
            "postal_code": buyer.postal_code,
            "settlement": buyer.settlement,
            "municipality": buyer.municipality,
            "country": buyer.country,
            "mobile_phone": buyer.mobile_phone,
            "email": buyer.email
        }
    })