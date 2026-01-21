from fastapi_mail import FastMail, MessageSchema
from app.config import conf, settings, CONTACT_INFO, BASE_URL

fm = FastMail(conf)


# -------------------------------
# Contact form laiškas
# -------------------------------
async def send_contact_message(email: str | None, phone: str | None):
    message = MessageSchema(
        subject="PRANEŠIMAS IŠ SVETAINĖS",
        recipients=[settings.MAIL_FROM],
        body=f"""
        <p><strong>SUSISIEKTI (contact-form)</strong></p>

        <p>
            El. paštas: {email or '-'}<br>
            Tel. numeris: {phone or '-'}</p>
        """,
        subtype="html",
    )
    await fm.send_message(message)


# -------------------------------
# Registracijos patvirtinimo laiškas
# -------------------------------
async def send_registration_confirmation_email(email: str, token: str):
    """
    Siunčia vartotojui registracijos patvirtinimo laišką su tokenu.
    """

    confirm_url = f"{BASE_URL}/login/confirm?token={token}"

    message = MessageSchema(
        subject="Prašome patvirtinti savo el. pašto adresą",
        recipients=[email],
        body=f"""
        <p>Sveiki,</p>

        <p>Jūsų paskyra sukurta.</p>

        <p>
            Kad sustiprintume Jūsų paskyros saugumą ir leistume Jums prie jos prisijungti pamiršus slaptažodį,
            prašome paspausti žemiau esančią nuorodą ir patvirtinti savo el. pašto {email} adresą.
        </p>

        <p> <strong>Patvirtinimo nuoroda:</strong>
            <a href="{confirm_url}" style="text-decoration: underline;">
                {confirm_url}
            </a>
        </p>

        <p>
            Jei per <strong>24 valandas</strong> neatliksite el. pašto patvirtinimo,
            registracijos procesas bus nutrauktas, o Jūsų paskyra automatiškai bus ištrinta.
        </p>

        <hr>
        
        
        <p>
            <strong>{CONTACT_INFO["company_name"]}</strong> | 
            tel. <a href="tel:{CONTACT_INFO["phone"]}">{CONTACT_INFO["phone"]}</a> | 
            el. paštas <a href="mailto:{CONTACT_INFO["email"]}">{CONTACT_INFO["email"]}</a>
        </p>
        """,
        subtype="html",
    )

    await fm.send_message(message)

# -------------------------------
# Sėkmingos registracijos laiškas
# -------------------------------
async def send_registration_success_email(email: str, login_id: str):
    login_url = f"{BASE_URL}/login"
    message = MessageSchema(
        subject="Prisijungimo duomenys",
        recipients=[email],
        body=f"""
        <p>Sveiki,</p>

        <p>
            Jūsų registracija sėkmingai užbaigta, galite jungtis prie informacinės sistemos.
        </p>

        <p>
            Jūsų prisijungimo ID kodas: <strong>{login_id}</strong>
        </p>
        
        <p>
            Jei nesate atidarę prisijungimo prie informacinės sistemos puslapio, jį galite pasiekti pasirinkę nuorodą
                <a href="{login_url}" style="text-decoration: underline;">
                    {login_url}
                </a>
        </p>

        <p style="margin: 0; font-size: 14px; line-height: 1.4;">
            <span style="
                display: inline-block;
                width: 16px;
                height: 16px;
                line-height: 16px;
                text-align: center;
                border: 2px solid red;
                border-radius: 50%;
                color: black;
                font-weight: bold;
                font-size: 12px;
                margin-right: 6px;
            ">!</span>
            Niekam neatskleiskite savo prisijungimo duomenų.
        </p>

        <hr>


        <p>
            <strong>{CONTACT_INFO["company_name"]}</strong> | 
            tel. <a href="tel:{CONTACT_INFO["phone"]}">{CONTACT_INFO["phone"]}</a> | 
            el. paštas <a href="mailto:{CONTACT_INFO["email"]}">{CONTACT_INFO["email"]}</a>
        </p>
        """,
        subtype="html",
    )

    await fm.send_message(message)


# -------------------------------
# Tokeno galiojimo pasibaigimo laiškas
# -------------------------------
async def send_confirmation_expired_email(email: str):
    message = MessageSchema(
        subject="Patvirtinimo nuoroda negalioja",
        recipients=[email],
        body=f"""
        <p>Sveiki,</p>

        <p>
            Bandėte patvirtinti savo el. pašto adresą, tačiau patvirtinimas neįvyko,
            nes patvirtinimo nuoroda yra neteisinga arba jos galiojimo laikas pasibaigęs.
        </p>

        <p>
            Prašome registruotis iš naujo.
        </p>

        <hr>


        <p>
            <strong>{CONTACT_INFO["company_name"]}</strong> | 
            tel. <a href="tel:{CONTACT_INFO["phone"]}">{CONTACT_INFO["phone"]}</a> | 
            el. paštas <a href="mailto:{CONTACT_INFO["email"]}">{CONTACT_INFO["email"]}</a>
        </p>
        """,
        subtype="html",
    )

    await fm.send_message(message)
