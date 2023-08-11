import os
import smtplib
from email.message import EmailMessage

subject = "Seš snitch? 🤔"


def body(link: str) -> str:
    return f"""Sorry, ale snitches ze sborovny nejsou vítaný. 😡<br>
    Takže koukej otevřít tenhle link, jinak dostaneš po čumáku.<br>
    <a href="https://muceni.porgovskadrbna.cz/nejsem-snitch/{link}">https://muceni.porgovskadrbna.cz/nejsem-snitch/{link}</a>
    <br><br>
    <i>Tvoje milovaná Drbna <3</i>
    """


def send_confirmation_email(email: str, link: str):
    msg = EmailMessage()

    msg["Subject"] = subject
    msg["From"] = "muceni@porgovskadrbna.cz"
    msg["To"] = email

    msg.set_content(body(link), subtype="html", charset="utf-8")

    with smtplib.SMTP_SSL("smtp.seznam.cz", 465) as server:
        server.login("muceni@porgovskadrbna.cz", os.getenv("EMAIL_PASSWORD"))
        server.send_message(msg, "muceni@porgovskadrbna.cz", email)
