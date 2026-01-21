from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.utils.helpers import read_text_from_file, convert_to_paragraphs
from app.config import templates, CONTACT_INFO

router = APIRouter()

@router.get("/privacy-policy", response_class=HTMLResponse)
async def privacy_policy_page(request: Request):
    raw_text = read_text_from_file("privacy-policy.txt")
    formatted_html = convert_to_paragraphs(raw_text, CONTACT_INFO)
    return templates.TemplateResponse("privacy-policy.html", {
        "request": request,
        "privacy_policy_html": formatted_html,
         "contact": CONTACT_INFO
    })

@router.get("/cookie-policy", response_class=HTMLResponse)
async def cookie_policy_page(request: Request):
    raw_text = read_text_from_file("cookie-policy.txt")
    formatted_html = convert_to_paragraphs(raw_text, CONTACT_INFO)
    return templates.TemplateResponse("cookie-policy.html", {
        "request": request,
        "cookie_policy_html": formatted_html,
        "contact": CONTACT_INFO
    })

@router.get("/accessibility", response_class=HTMLResponse)
async def accessibility_page(request: Request):
    raw_text = read_text_from_file("accessibility.txt")
    formatted_html = convert_to_paragraphs(raw_text, CONTACT_INFO)
    return templates.TemplateResponse("accessibility.html", {
        "request": request,
        "accessibility_html": formatted_html,
        "contact": CONTACT_INFO
    })
