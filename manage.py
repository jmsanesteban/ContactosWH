#!/usr/bin/env python3
"""
manage.py — CLI para inicializar la base de datos y gestionar el sistema.

Uso:
  python manage.py init_db          # Crea tablas y admin por defecto
  python manage.py create_admin     # Crea un nuevo admin
  python manage.py reset_password <username>
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.extensions import db
from app.models.user import User
from app.utils.security import generate_secure_password


def init_db():
    """Crea todas las tablas y el usuario admin inicial."""
    app = create_app(os.environ.get('FLASK_ENV', 'production'))
    with app.app_context():
        db.create_all()
        print('[OK] Tablas creadas.')

        if not User.query.filter_by(username='admin').first():
            password = generate_secure_password()
            admin = User(
                username='admin',
                email='admin@contactoswh.local',
                role='admin',
                is_active=True,
                must_change_password=True,
            )
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            print(f'\n[ADMIN CREADO]')
            print(f'  Usuario   : admin')
            print(f'  Contraseña: {password}')
            print(f'  (Cambia la contraseña en el primer inicio de sesión)\n')
        else:
            print('[INFO] El usuario admin ya existe.')


def create_admin(username=None, email=None):
    """Crea un nuevo usuario administrador."""
    app = create_app(os.environ.get('FLASK_ENV', 'production'))
    with app.app_context():
        username = username or input('Nombre de usuario: ').strip()
        email = email or input('Email: ').strip()
        password = generate_secure_password()
        user = User(username=username, email=email, role='admin',
                    is_active=True, must_change_password=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f'\n[ADMIN CREADO] {username} / {password}\n')


def reset_password(username):
    app = create_app(os.environ.get('FLASK_ENV', 'production'))
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f'[ERROR] Usuario "{username}" no encontrado.')
            sys.exit(1)
        password = generate_secure_password()
        user.set_password(password)
        user.must_change_password = True
        db.session.commit()
        print(f'\n[CONTRASEÑA RESTABLECIDA] {username} / {password}\n')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else None
    if cmd == 'init_db':
        init_db()
    elif cmd == 'create_admin':
        create_admin()
    elif cmd == 'reset_password' and len(sys.argv) > 2:
        reset_password(sys.argv[2])
    else:
        print(__doc__)
