from flask import Flask
from .extensions import db, login_manager, mail, migrate


def create_app(test_config=None) -> Flask:
    """Возвращает приложение с подключенной базой данных и системой входа, запускается в run.py"""

    app = Flask(__name__)
    app.config.from_object('config.Config')
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'user.login'  # Отправление незалогиненного пользователя на страницу входа
    login_manager.login_message_category = 'info'  # Тип сообщения info
    mail.init_app(app)

    # Подключение маршрутов к приложению
    from .routes import main_bp, user_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp)

    migrate.init_app(app, db)

    return app
