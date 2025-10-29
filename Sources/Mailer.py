import os
import ssl, smtplib, base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class Mailer:
    def __init__(self, server: str, port: int):
        self.server = server
        self.port = int(port)

        self.user = os.getenv("EMAIL_USER")
        self.password = os.getenv("EMAIL_PASS")
        self.sender = os.getenv("EMAIL_FROM")
        self.to = os.getenv("EMAIL_TO")

    def _auth_plain(self, s: smtplib.SMTP):
        """强制 AUTH PLAIN，避开非标准 LOGIN 提示"""
        auth_bytes = f"\0{self.user}\0{self.password}".encode("utf-8")
        auth_b64 = base64.b64encode(auth_bytes).decode("ascii")
        code, resp = s.docmd("AUTH", "PLAIN " + auth_b64)
        if code != 235:
            raise smtplib.SMTPAuthenticationError(code, resp)

    def SendMarkdown(self, subject: str, markdownText: str):
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = self.to
        msg.attach(MIMEText(markdownText, "plain", "utf-8"))

        ctx = ssl.create_default_context()

        if self.port == 465:
            with smtplib.SMTP_SSL(self.server, self.port, context=ctx, timeout=30) as s:
                s.ehlo()
                try:
                    s.login(self.user, self.password)
                except AttributeError:
                    # 部分服务器的 LOGIN 提示不标准：退而求其次走 AUTH PLAIN
                    self._auth_plain(s)
                s.send_message(msg)
        else:
            with smtplib.SMTP(self.server, self.port, timeout=30) as s:
                s.ehlo()
                s.starttls(context=ctx)
                s.ehlo()
                try:
                    s.login(self.user, self.password)
                except AttributeError:
                    self._auth_plain(s)
                s.send_message(msg)
