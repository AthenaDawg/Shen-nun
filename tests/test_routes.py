from app.models import User
from app.extensions import db


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Добро пожаловать на сайт чая!".encode('utf-8') in response.data


def test_login_page(client):
    response = client.get("/user/login")
    assert response.status_code == 200
    assert "Войти".encode('utf-8') in response.data


def test_register_page(client):
    response = client.get("/user/register")
    assert response.status_code == 200
    assert "Регистрация".encode('utf-8') in response.data


def test_registration_valid(client):
    response = client.post('/user/register', data={
        'username': 'denis',
        'email': 'denis@example.com',
        'password': 'Pass1234',
        'confirm_password': 'Pass1234'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Спасибо за регистрацию'.encode('utf-8') in response.data


def test_registration_invalid_email(client):
    response = client.post('/user/register', data={
        'username': 'denis',
        'email': 'invalid-email',
        'password': 'Pass1234',
        'confirm_password': 'Pass1234'
    })

    assert b'Invalid email' in response.data or 'Некорректный email'.encode('utf-8t') in response.data


def test_registration_password_mismatch(client):
    response = client.post('/user/register', data={
        'username': 'denis',
        'email': 'denis@example.com',
        'password': 'Pass1234',
        'confirm_password': 'WrongPass'
    })

    assert b'Field must be equal' in response.data or 'Пароли должны совпадать'.encode('utf-8') in response.data


def test_registration_short_username(client):
    response = client.post('/user/register', data={
        'username': 'a',  # слишком короткое имя
        'email': 'denis@example.com',
        'password': 'Pass1234',
        'confirm_password': 'Pass1234'
    })
    assert b'Field must be between 2 and 20 characters long' in response.data


def test_registration_long_username(client):
    response = client.post('/user/register', data={
        'username': 'a' * 30,  # слишком длинное имя
        'email': 'denis@example.com',
        'password': 'Pass1234',
        'confirm_password': 'Pass1234'
    })
    assert b'Field must be between 2 and 20 characters long' in response.data


def test_registration_password_without_digit(client):
    response = client.post('/user/register', data={
        'username': 'denis',
        'email': 'denis@example.com',
        'password': 'Password',  # нет цифр
        'confirm_password': 'Password'
    })
    assert 'Пароль должен содержать хотя бы одну букву и одну цифру.'.encode('utf-8') in response.data


def test_registration_password_without_letter(client):
    response = client.post('/user/register', data={
        'username': 'denis',
        'email': 'denis@example.com',
        'password': '12345678',  # нет букв
        'confirm_password': '12345678'
    })
    assert 'Пароль должен содержать хотя бы одну букву и одну цифру.'.encode('utf-8') in response.data


def test_login_valid(client, app):
    with app.app_context():
        user = User(username='denis', email='denis@example.com', is_confirmed=True)
        user.set_password('Pass1234')
        db.session.add(user)
        db.session.commit()

    response = client.post('/user/login', data={
        'email': 'denis@example.com',
        'password': 'Pass1234'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Вы успешно вошли!'.encode('utf-8') in response.data


def test_login_invalid_password(client, app):
    with app.app_context():
        user = User(username='denis', email='denis@example.com')
        user.set_password('Pass1234')
        db.session.add(user)
        db.session.commit()

    response = client.post('/user/login', data={
        'email': 'denis@example.com',
        'password': 'WrongPass'
    })

    assert 'Неверный'.encode('utf-8') in response.data


def test_login_empty_fields(client):
    response = client.post('/user/login', data={
        'email': '',
        'password': ''
    })
    assert 'Это поле обязательно'.encode('utf-8') in response.data


def test_request_password_reset(client, app):
    with app.app_context():
        user = User(username='denis', email='denis@example.com')
        user.set_password('Pass1234')
        db.session.add(user)
        db.session.commit()

    response = client.post('/user/reset_password', data={
        'email': 'denis@example.com'
    }, follow_redirects=True)

    assert 'отправлено на вашу почту'.encode('utf-8') in response.data


def test_request_password_reset_invalid_email(client):
    response = client.post('/user/reset_password', data={
        'email': 'not-an-email'
    })
    assert b'Invalid email address' in response.data or 'Некорректный email'.encode('utf-8p') in response.data


def test_reset_password(client, app):
    with app.app_context():
        user = User(username='denis', email='denis@example.com')
        user.set_password('Pass1234')
        db.session.add(user)
        db.session.commit()
        token = user.get_reset_token()

    response = client.post(f'/user/reset_password/{token}', data={
        'password': 'Newpass123',
        'confirm_password': 'Newpass123'
    }, follow_redirects=True)

    assert 'пароль был успешно обновлён'.encode('utf-8') in response.data


def test_reset_password_mismatch(client, app):
    with app.app_context():
        user = User(username='denis', email='denis@example.com')
        user.set_password('Pass1234')
        db.session.add(user)
        db.session.commit()
        token = user.get_reset_token()

    response = client.post(f'/user/reset_password/{token}', data={
        'password': 'Newpass123',
        'confirm_password': 'Mismatch123'
    })

    assert 'Пароли должны совпадать.'.encode('utf-8') in response.data


