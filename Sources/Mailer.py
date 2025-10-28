import os
import ssl, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class Mailer:
    def __init__(self, server:str, port:int):
        self.server = server
        self.port = port
        self.user = os.getenv("EMAIL_USER")
        self.password = os.getenv("EMAIL_PASS")
        self.sender = os.getenv("EMAIL_FROM")
        self.to = os.getenv("EMAIL_TO")

    def SendMarkdown(self, subject : str, markdownText : str):
        msg = MIMEMultipart("alternative")
        msg["Subject"]=subject; msg["From"]=self.sender; msg["To"]=self.to
        msg.attach(MIMEText(markdownText, "plain", "utf-8"))
        if self.port==465:
            ctx=ssl.create_default_context()
            with smtplib.SMTP_SSL(self.server, self.port, context=ctx) as s:
                s.connect(self.server)
                s.login(self.user, self.password); s.send_message(msg)
        else:
            with smtplib.SMTP(self.server, self.port) as s:
                s.starttls(); s.login(self.user, self.password); s.send_message(msg)
