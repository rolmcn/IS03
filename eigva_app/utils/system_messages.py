from eigva_app.config import CONTACT_INFO
from eigva_app.models import User

class SystemMessages:

    @staticmethod
    def super_user_first_login_message(user: User) -> str:
        return (
            "Sveikiname prisijungus prie informacinės sistemos EIGVA! 🎉<br><br>"
            "Jums yra priskirtos 'Super naudotojo' teisės.<br>"
            "Kad galėtumėte naudotis informacine sistema:<br>"
            "1. Sukurkite mokėtoją (meniu 'Paskyra' → 'Mokėtojas').<br>"
            "2. Įsigykite licencijas (meniu 'Paskyra' → 'Licencijos').<br>"
            "3. Papildykite savo kontaktinę informaciją ir, jei reikia, pridėkite kitus naudotojus (meniu 'Paskyra' → 'Naudotojai').<br>"
            "4. Atlikite sistemos nustatymus (meniu 'Paskyra' → 'Nustatymai').<br><br>"
            "Naudotojo vadovą rasite meniu 'Žinynas'.<br><br>"
            "Linkime sėkmės!<br>"
            f"<strong>{CONTACT_INFO['company_name']}</strong> | "
            f"tel. <a href='tel:{CONTACT_INFO['phone']}'>{CONTACT_INFO['phone']}</a> | "
            f"el. paštas <a href='mailto:{CONTACT_INFO['email']}'>{CONTACT_INFO['email']}</a>"
        )

    @staticmethod
    def user_first_login_message(user: User) -> str:
        return (
            "Sveikiname prisijungus prie informacinės sistemos EIGVA! 🎉<br><br>"
            "Naudotojo vadovą rasite meniu 'Žinynas'.<br>"
            "Esant klausimams kreikitės į 'Super naudotoją' ('Super naudotojai nurodomi meniu 'Paskyra' → 'Naudotojai').<br><br>"
            "Linkime sėkmės!<br>"
            f"<strong>{CONTACT_INFO['company_name']}</strong>"
        )
