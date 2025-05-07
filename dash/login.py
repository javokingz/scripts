from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from .models import db, User

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash('Por favor verifica tu usuario y contraseña e intenta de nuevo.')
            return redirect(url_for('auth.login'))

        login_user(user, remember=remember)
        return redirect(url_for('main.dashboard'))

    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')

        # Validaciones
        if password != password2:
            flash('Las contraseñas no coinciden.')
            return redirect(url_for('auth.register'))

        # Verificar si el usuario ya existe
        user = User.query.filter_by(username=username).first()
        if user:
            flash('El nombre de usuario ya está en uso.')
            return redirect(url_for('auth.register'))

        # Verificar si el email ya existe
        user = User.query.filter_by(email=email).first()
        if user:
            flash('El correo electrónico ya está registrado.')
            return redirect(url_for('auth.register'))

        # Crear nuevo usuario
        new_user = User(username=username, email=email)
        new_user.set_password(password)

        # Guardar en la base de datos
        db.session.add(new_user)
        db.session.commit()

        flash('¡Registro exitoso! Ahora puedes iniciar sesión.')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
