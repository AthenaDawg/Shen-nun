from flask_mail import Message
from flask import url_for, current_app
from app import mail
import logging


def send_reset_password_email(user: 'User') -> None:
    """Создает письмо с токеном пользователю"""
    token = user.get_reset_token()
    msg = Message('Сброс пароля',
                  sender=current_app.config['MAIL_USERNAME'],
                  recipients=[user.email])
    msg.body = (
        f"Здравствуйте!\n\n"
        f"Чтобы сбросить пароль, перейдите по ссылке:\n"
        f"{url_for('user.reset_token', token=token, _external=True)}\n\n"
        "Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.\n\n"
        "С уважением,\nКоманда сайта"
    )

    msg.html = (
        f"<p>Здравствуйте!</p>"
        f"<p>Чтобы сбросить пароль, перейдите по ссылке:</p>"
        f'<p><a href="{url_for("user.reset_token", token=token, _external=True)}">'
        "Сбросить пароль</a></p>"
        "<p>Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.</p>"
        "<p>С уважением,<br>Команда сайта</p>"
    )

    try:
        mail.send(msg)
    except Exception as e:
        logging.error(f"Ошибка при отправке письма подтверждения почты пользователю {user.email}: {e}")


def send_email_confirm_token(user: 'User') -> None:
    token = user.get_email_confirm_token()
    msg = Message('Подтверждение электронной почты',
                  sender=current_app.config['MAIL_USERNAME'],
                  recipients=[user.email])

    msg.body = (
        f"Здравствуйте!\n\n"
        f"Чтобы подтвердить вашу почту, перейдите по ссылке:\n"
        f"{url_for('user.confirm_email_token', token=token, _external=True)}\n\n"
        "Если вы не пытались зарегистрироваться на сайте, просто проигнорируйте это письмо.\n\n"
        "С уважением,\nКоманда сайта"
    )

    msg.html = (
        f"<p>Здравствуйте!</p>"
        f"<p>Чтобы подтвердить вашу почту, перейдите по ссылке:</p>"
        f'<p><a href="{url_for("user.confirm_email_token", token=token, _external=True)}">'
        "Подтвердить почту</a></p>"
        "<p>Если вы не пытались зарегистрироваться на сайте, просто проигнорируйте это письмо.</p>"
        "<p>С уважением,<br>Команда сайта</p>"
    )

    try:
        mail.send(msg)
    except Exception as e:
        logging.error(f"Ошибка при отправке письма подтверждения почты пользователю {user.email}: {e}")


