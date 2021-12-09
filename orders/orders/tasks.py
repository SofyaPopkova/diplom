from .settings import EMAIL_HOST_USER
from django.core.mail.message import EmailMultiAlternatives
from .celery import app


@app.task()
def send_email(title, message: str, email: str):
    email_list = list()
    email_list.append(email)
    try:
        message = EmailMultiAlternatives(subject=title, body=message, from_email=EMAIL_HOST_USER, to=email_list)
        message.send()
        return f'Тема: {message.subject}, Письмо:{message.body}'
    except Exception:
        raise Exception
