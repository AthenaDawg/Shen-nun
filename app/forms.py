from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.fields.simple import BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp


class RegistrationForm(FlaskForm):
    """Форма регистрации пользователя"""

    username = StringField('Имя пользователя', validators=[DataRequired(message="Это поле обязательно"),
                                                           Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(message="Это поле обязательно"), Email(), Length(max=60)])
    password = PasswordField('Пароль', validators=[DataRequired(message="Это поле обязательно"), Length(min=6),
                                                   Regexp(r'(?=.*[A-Za-z])(?=.*\d)',
    message="Пароль должен содержать хотя бы одну букву и одну цифру.")])
    confirm_password = PasswordField('Повторите пароль', validators=[DataRequired(message="Это поле обязательно"),
                                                                     EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    """Форма входа пользователя."""

    email = StringField('Email', validators=[DataRequired(message="Это поле обязательно"), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(message="Это поле обязательно")])
    remember = BooleanField('Запомнить меня')  # Чекбокс для запоминания авторизации
    submit = SubmitField('Войти')


class RequestResetForm(FlaskForm):
    """Форма сброса пароля"""
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Сбросить пароль")


class ResetPasswordForm(FlaskForm):
    """Форма для установки нового пароля после сброса через email"""

    password = PasswordField('Новый пароль', validators=[
        DataRequired(message="Это поле обязательно"), Length(min=6),
        Regexp(r'(?=.*[A-Za-z])(?=.*\d)', message="Пароль должен содержать хотя бы одну букву и одну цифру.")
    ])
    confirm_password = PasswordField('Повторите новый пароль', validators=[
        DataRequired(message="Это поле обязательно"),
        EqualTo('password', message='Пароли должны совпадать.')
    ])
    submit = SubmitField('Сменить пароль')


class RepeatEmailConfirmationForm(FlaskForm):
    """Повторный запрос отправки письма для подтверждения почты"""
    submit = SubmitField("Отправить письмо повторно")




