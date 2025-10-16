from flask import (Blueprint, request, redirect, url_for, flash,
                   render_template, session)
from flask_login import login_user, logout_user, current_user, login_required
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, or_

from .models import User
from app import db, login_manager
from .forms import RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm, RepeatEmailConfirmationForm
from app.email_utils import send_reset_password_email, send_email_confirm_token
from datetime import datetime, timezone, timedelta

# Создание основного и пользовательского блупринтов маршрутов
main_bp = Blueprint('main', __name__)
user_bp = Blueprint('user', __name__, url_prefix="/user")


# TODO: Переписать авторизацию на JWT + API вместо сессий для SPA и мобильных клиентов

def get_user_by_email(email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    return db.session.execute(stmt).scalars().first()


@main_bp.route('/')
def home():
    """Обрабатывает домашнюю страницу"""

    return render_template('home.html')


@user_bp.route('register', methods=['GET', 'POST'])
def register():
    """Обрабатывает страницу регистрации пользователя"""

    form = RegistrationForm()

    # Проверка есть ли уже в БД данный пользователь
    if form.validate_on_submit():
        stmt = select(User).where(
            or_(
                User.username == form.username.data,
                User.email == form.email.data
            )
        )

        existing_user = db.session.execute(stmt).scalars().first()

        if existing_user:
            flash('Пользователь с таким именем или email уже существует', 'danger')
            return redirect(url_for('user.register'))

        # Если пользователь новый, он внесен в БД
        new_user = User(
            username=form.username.data,
            email=form.email.data,
        )
        new_user.set_password(form.password.data)
        session['email'] = new_user.email

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Регистрация прошла успешно! На вашу почту отправлено письмо для подтверждения.', 'success')
            send_email_confirm_token(new_user)
            # Храним время отправки письма в сессии для ограничения спама письмами
            session["last_confirmation_email"] = datetime.now(timezone.utc).isoformat()
        except SQLAlchemyError:
            db.session.rollback()
            flash('Ошибка при регистрации. Попробуйте позже.', 'danger')
            return redirect(url_for('user.register'))

        return redirect(url_for('user.confirm_email_info'))

    return render_template('register.html', form=form)


@login_manager.user_loader
def load_user(user_id):
    """Загружает пользователя по ID для Flask-Login (поддержка сессий и авторизации)"""
    return db.session.get(User, user_id)


@user_bp.route('login', methods=['GET', 'POST'])
def login():
    """Проверяет форму по валидации, логинит пользователя"""

    is_password_requested = session.get("is_password_reset_requested")  # Запрошен ли сброс пароля

    # Если пользователь авторизован, он перенаправлен на домашнюю страницу
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        # Поиск пользователя в БД по введенной почте и проверка пароля (валидация)
        try:
            user = get_user_by_email(email)
        except SQLAlchemyError:
            flash("Произошла ошибка при подключении к базе данных. Попробуйте позже.")
            return redirect(url_for("user.login"))

        if user and user.check_password(password):
            if user.is_confirmed:
                login_user(user, remember=form.remember.data)
                session.pop('email', None)
                session.pop('last_confirmation_email', None)
                flash('Вы успешно вошли!', 'success')
                next_page = request.args.get('next')  # Получение URL-а, куда пользователь хотел перейти до авторизации
                return redirect(next_page) if next_page else redirect(url_for('main.home'))
            else:
                flash('Пожалуйста, подтвердите вашу почту перед входом.', 'warning')
                current_time = datetime.now(timezone.utc)
                session['last_confirmation_email'] = current_time.isoformat()
                return redirect(url_for('user.confirm_email_info'))
        else:
            flash('Неверный email или пароль', 'danger')

    if is_password_requested:
        session.pop("is_password_reset_requested", None)

    return render_template('login.html', form=form, is_password_requested=is_password_requested)


@user_bp.route('logout')
@login_required
def logout():
    """Разлогинивает пользователя и очищает сессию"""
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('main.home'))


@user_bp.route('reset_password', methods=['GET', 'POST'])
def reset_request():
    """Отправляет пользователю письмо с токеном для сброса пароля"""
    form = RequestResetForm()

    if form.validate_on_submit():
        email = form.email.data
        session['email'] = email
        last_sent = session.get('last_reset_request')
        current_time = datetime.now(timezone.utc)

        if last_sent and (current_time - datetime.fromisoformat(last_sent)) < timedelta(seconds=60):
            flash("Подождите немного перед повторной отправкой письма", "warning")
            return redirect(url_for('user.reset_request'))

        try:
            user = get_user_by_email(email)
        except SQLAlchemyError:
            flash("Произошла ошибка при подключении к базе данных. Попробуйте позже.")
            return redirect(url_for("user.login"))

        if user:
            send_reset_password_email(user)
            session["last_reset_request"] = datetime.now(timezone.utc).isoformat()
            flash('Письмо с инструкциями по сбросу пароля отправлено на вашу почту.', 'info')
            session['is_password_reset_requested'] = True
            return redirect(url_for('user.login'))
        else:
            flash('Пользователь с таким email не найден.', 'warning')

    return render_template('reset_request.html', form=form, email_value=session.get('email', ''))


@user_bp.route('reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    """Обрабатывает сброс пароля пользователя по предоставленному токену"""

    try:
        user = User.verify_reset_token(token)  # Попытка расшифровать токен и получить пользователя
    except SQLAlchemyError:
        flash("Произошла ошибка при подключении к базе данных. Попробуйте позже.", 'danger')
        return redirect(url_for('user.login'))

    if user is None:
        flash('Ссылка для сброса пароля недействительна или устарела.', 'warning')
        return redirect(url_for('user.reset_request'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)  # Установка нового хэшированного пароля
        try:
            db.session.commit()
            flash('Ваш пароль был успешно обновлён. Теперь вы можете войти.', 'success')
            session.pop('email', None)
            session.pop('last_reset_request', None)
            return redirect(url_for('user.login'))
        except SQLAlchemyError:
            db.session.rollback()
            flash("Не удалось обновить пароль. Попробуйте позже.", 'danger')
            return redirect(url_for('user.reset_request'))

    return render_template('reset_token.html', form=form)


@user_bp.route('/confirm_email', methods=['GET', 'POST'])
def confirm_email_info():
    """Отправляет повторное сообщение на почту пользователя с ее подтверждением"""
    form = RepeatEmailConfirmationForm()
    if form.validate_on_submit():
        email = session.get('email')
        last_sent = session.get("last_confirmation_email")
        current_time = datetime.now(timezone.utc)

        if last_sent and (current_time - datetime.fromisoformat(last_sent)) < timedelta(seconds=60):
            flash("Подождите немного перед повторной отправкой письма", "warning")
            return redirect(url_for('user.confirm_email_info'))

        try:
            user = get_user_by_email(email)
        except SQLAlchemyError:
            flash("Произошла ошибка при подключении к базе данных. Попробуйте позже.", 'danger')
            return redirect(url_for("user.confirm_email_info"))

        if user:
            send_email_confirm_token(user)
            session['last_confirmation_email'] = current_time.isoformat()
            flash("Повторное письмо было отправлено вам на почту", "success")
        else:
            flash("Пользователь не найден", "danger")

        return redirect(url_for('user.confirm_email_info'))
    return render_template('confirm_email.html', form=form)


@user_bp.route('/confirm_email/<token>', methods=['GET', 'POST'])
def confirm_email_token(token):
    """Подтверждает подлинность почты пользователя"""
    try:
        user = User.verify_email_confirm_token(token)  # Попытка расшифровать токен и получить пользователя
    except SQLAlchemyError:
        flash("Произошла ошибка при подключении к базе данных. Попробуйте позже.", 'danger')
        return redirect(url_for('user.register'))

    if user:

        if user.is_confirmed:
            flash("Почта уже подтверждена", 'info')
        else:
            user.is_confirmed = True

        try:
            db.session.commit()
            flash("Вы успешно зарегестрированы", 'success')
        except SQLAlchemyError:
            db.session.rollback()
            flash("Ошибка при подтверждении email. Попробуйте позже.", 'danger')
            return redirect(url_for('user.register'))
        return redirect(url_for('main.home'))

    else:
        flash("Почтовый ящик не найден", 'danger')
        return redirect(url_for('user.register'))


@main_bp.route('/profile')
@login_required
def profile():
    return 'Это защищённая страница для залогиненных пользователей'




