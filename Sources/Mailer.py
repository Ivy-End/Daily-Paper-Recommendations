import ssl, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class Mailer:
    def __init__(self, server:str, port:int, user:str, password:str, sender:str, to:str):
        self.server, self.port, self.user, self.password = server, port, user, password
        self.sender, self.to = sender, to

    def SendMarkdown(self, subject : str, markdownText : str):
        msg = MIMEMultipart("alternative")
        msg["Subject"]=subject; msg["From"]=self.sender; msg["To"]=self.to
        msg.attach(MIMEText(md_text, "plain", "utf-8"))
        if self.port==465:
            ctx=ssl.create_default_context()
            with smtplib.SMTP_SSL(self.server, self.port, context=ctx) as s:
                s.login(self.user, self.password); s.send_message(msg)
        else:
            with smtplib.SMTP(self.server, self.port) as s:
                s.starttls(); s.login(self.user, self.password); s.send_message(msg)
