import logging
from typing import Annotated

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from eigva_app.database import get_async_session
from eigva_app.models import Payer, User
from eigva_app.schemas.payer_schemas import PayerSchema
from eigva_app.core.security.crypto import encrypt_data, hash_full_name_email, hash_identification_code, hash_vat_code
from eigva_app.services.account_service import get_user_messages, mark_message_read
from eigva_app.utils.choices_municipalities import MUNICIPALITIES
from eigva_app.core.security.auth import get_current_user, get_current_payer
from eigva_app.config import templates

logger = logging.getLogger(__name__)
router = APIRouter()

# ---------------------
# Depends tipai
# ---------------------
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentPayer = Annotated[Payer, Depends(get_current_payer)]
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]


# ---------------- GET ACCOUNT PAGE ----------------
@router.get("/account", response_class=HTMLResponse)
async def account_page(
    request: Request,
    current_user: CurrentUser,
    current_payer: CurrentPayer,
    session: SessionDep,
):

    messages = await get_user_messages(session, current_user.id)
    success_message = request.query_params.get("success")
    error_message = request.query_params.get("error")
    active_tab = request.query_params.get("active_tab")

    scenario = None
    if current_payer.status == "pending":
        scenario = "pending"
    elif current_payer.status == "active":
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
            "current_payer": {
                "payer_type": current_payer.payer_type,
                "full_name": current_payer.full_name,
                "identification_code": current_payer.identification_code,
                "vat_status": current_payer.vat_status,
                "vat_code": current_payer.vat_code,
                "street": current_payer.street,
                "house_number": current_payer.house_number,
                "apartment_number": current_payer.apartment_number,
                "postal_code": current_payer.postal_code,
                "settlement": current_payer.settlement,
                "municipality": current_payer.municipality,
                "country": current_payer.country,
                "mobile_phone": current_payer.mobile_phone,
                "email": current_payer.email,
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


# ---------------- SAVE PAYER ----------------
@router.post("/account/save_payer")
async def save_payer(
    request: Request,
    session: SessionDep,
    current_payer: CurrentPayer
):
    data = await request.form()
    form_data = dict(data)
    field_errors = {}

    # -----------------------------
    # 1. Pydantic validacija
    # -----------------------------
    try:
        payer_schema = PayerSchema(**form_data)
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

    if payer_schema.payer_type == "physical":
        full_name_email_hash_val = hash_full_name_email(
            payer_schema.full_name, payer_schema.email
        )
        result = await session.execute(
            select(Payer).where(
                Payer.full_name_email_hash == full_name_email_hash_val,
                            Payer.id != current_payer.id
            )
        )
        if result.scalars().first():
            duplicates["email"] = "Mokėtojas su tokiu el. pašto adresu jau egzistuoja"

    if payer_schema.payer_type == "legal" and payer_schema.identification_code:
        ident_hash_val = hash_identification_code(payer_schema.identification_code)
        result = await session.execute(
            select(Payer).where(
                Payer.identification_code_hash == ident_hash_val,
                Payer.id != current_payer.id
            )
        )
        if result.scalars().first():
            duplicates["identification_code"] = (
                "Toks mokėtojas jau egzistuoja. Patikrinkite ar teisingai nurodytas įmonės kodas."
            )

    if payer_schema.vat_status == "yes" and payer_schema.vat_code:
        vat_hash_val = hash_vat_code(payer_schema.vat_code)
        result = await session.execute(
            select(Payer).where(
                Payer.vat_code_hash == vat_hash_val,
                Payer.id != current_payer.id
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
    payer_data = {
        "payer_type": payer_schema.payer_type,
        "vat_status": payer_schema.vat_status,
        "municipality": payer_schema.municipality,
        "full_name_encrypted": encrypt_data(payer_schema.full_name),
        "identification_code_encrypted": encrypt_data(payer_schema.identification_code) if payer_schema.identification_code else None,
        "vat_code_encrypted": encrypt_data(payer_schema.vat_code) if payer_schema.vat_code else None,
        "street_encrypted": encrypt_data(payer_schema.street),
        "house_number_encrypted": encrypt_data(payer_schema.house_number),
        "apartment_number_encrypted": encrypt_data(payer_schema.apartment_number) if payer_schema.apartment_number else None,
        "postal_code_encrypted": encrypt_data(payer_schema.postal_code),
        "settlement_encrypted": encrypt_data(payer_schema.settlement),
        "mobile_phone_encrypted": encrypt_data(payer_schema.mobile_phone) if payer_schema.mobile_phone else None,
        "email_encrypted": encrypt_data(payer_schema.email),
        "full_name_email_hash": full_name_email_hash_val,
        "identification_code_hash": ident_hash_val,
        "vat_code_hash": vat_hash_val,
        "status": "active",
    }

    # -----------------------------
    # 4. Įrašymas į DB
    # -----------------------------
    try:
        payer = current_payer
        for key, value in payer_data.items():
            # Tikriname, ar objektas turi property su setteriu
            prop = getattr(type(payer), key, None)
            if isinstance(prop, property) and prop.fset:
                setattr(payer, key, value)  # property su setteriu
            elif hasattr(payer, key):
                setattr(payer, key, value)  # tiesiog column (_encrypted ar kiti)
            # jei nėra column ir nėra setterio – ignoruojame
        await session.commit()
        await session.refresh(payer)
    except IntegrityError as e:
        await session.rollback()
        logger.error(f"DB integrity error: {e}")
        scenario = "saving-error"
        return JSONResponse({"scenario": scenario})
    except Exception as e:
        await session.rollback()
        logger.exception(f"Unexpected error while saving payer: {e}")
        scenario = "server-error"
        return JSONResponse({"scenario": scenario})

    # -----------------------------
    # 5. Sėkmės pranešimas
    # -----------------------------
    scenario = "success"
    return JSONResponse({
        "scenario": scenario,
        "payer": {
            "payer_type": payer.payer_type,
            "full_name": payer.full_name,
            "identification_code": payer.identification_code,
            "vat_code": payer.vat_code,
            "street": payer.street,
            "house_number": payer.house_number,
            "apartment_number": payer.apartment_number,
            "postal_code": payer.postal_code,
            "settlement": payer.settlement,
            "municipality": payer.municipality,
            "country": payer.country,
            "mobile_phone": payer.mobile_phone,
            "email": payer.email
        }
    })