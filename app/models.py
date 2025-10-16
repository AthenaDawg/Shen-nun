from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import current_app
from itsdangerous import URLSafeTimedSerializer as Serializer
from itsdangerous import BadSignature, SignatureExpired
from app import db
from typing import Optional
from datetime import datetime, timezone


class User(UserMixin, db.Model):
    """Модель пользователя для базы данных"""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    role = db.Column(db.String(20), nullable=False, default='user')

    def set_password(self, password: str) -> None:
        """Хэширует пароль и сохраняет его"""

        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Проверяет, совпадает ли введённый пароль с сохранённым хэшем"""

        return check_password_hash(self.password_hash, password)

    def get_reset_token(self) -> str:
        """Генерирует токен для сброса пароля"""

        s = Serializer(current_app.config['SECRET_KEY'])  # Создание объекта для подписи токена
        return s.dumps({'user_id': self.id})  # Преобразование ID пользователя в токен

    @staticmethod  # Метод не требующий создания объекта
    def verify_reset_token(token: str, max_age=3600) -> Optional['User']:
        """Проверяет токен и возвращает User, если он валиден. Объявляет срок действия"""

        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=max_age)
            user_id = data['user_id']  # Расшифровка и извлечение токена
            return db.session.get(User, user_id)
        except (BadSignature, SignatureExpired):
            return None

    def get_email_confirm_token(self) -> str:
        """Генерирует токен для подтверждения почты"""
        s = Serializer(current_app.config['SECRET_KEY'])
        # Преобразование ID пользователя в токен
        return s.dumps({'user_id': self.id, 'timestamp': datetime.now(timezone.utc).isoformat()})

    @staticmethod
    def verify_email_confirm_token(token: str, max_age=3600) -> Optional['User']:
        """Проверяет токен и возвращает User, если он валиден. Объявляет срок действия"""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=max_age)
            user_id = data['user_id']
            return db.session.get(User, user_id)
        except (BadSignature, SignatureExpired):
            return None





