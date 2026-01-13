import logging.handlers
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
        # max_level deve receber o nome do level, mas quero o número
        super().__init__()

        # self.max_level terá o número do level
        self.max_level = logging.getLevelNamesMapping().get(max_level.upper(), 50)

    def filter(self, record: logging.LogRecord) -> bool:
        # Retorna True se o nível do registro for menor ou igual ao nível máximo permitido
        return record.levelno <= self.max_level