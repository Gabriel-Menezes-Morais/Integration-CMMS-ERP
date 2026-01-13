# Arquivo: custom_log.py
import logging.handlers
import smtplib
from email.utils import formatdate

class SSLSMTPHandler(logging.handlers.SMTPHandler):
    def emit(self, record):
        try:
            import smtplib
            try:
                msg = self.format(record)
            except Exception:
                self.handleError(record)
                return

            email_msg = (
                f"From: {self.fromaddr}\r\n"
                f"To: {','.join(self.toaddrs)}\r\n"
                f"Subject: {self.getSubject(record)}\r\n"
                f"Date: {formatdate()}\r\n"
                f"\r\n{msg}"
            )

            # Conexão SSL direta (Porta 465)
            smtp = smtplib.SMTP_SSL(self.mailhost, self.mailport, timeout=self.timeout)
            
            if self.username:
                smtp.login(self.username, self.password)
            
            smtp.sendmail(self.fromaddr, self.toaddrs, email_msg.encode('utf-8'))
            smtp.quit()
        except Exception:
            self.handleError(record)

class MaxLevelFilter(logging.Filter):
    def __init__(self, max_level: str) -> None:
        # max_level é um argumento adicional que coloquei
        # max_level deve receber o nome do level, mas quero o número
        super().__init__()

        # self.max_level terá o número do level
        self.max_level = logging.getLevelNamesMapping().get(max_level.upper(), 50)

    def filter(self, record: logging.LogRecord) -> bool:
        # record é o LogRecord que eu disse antes
        # record.levelno é o número do level do log
        # se o número do level do log for menor ou igual ao max_level que
        # definimos no filter o log passa.
        # INFO 20 só aceitará logs INFO e DEBUG.
        return record.levelno <= self.max_level