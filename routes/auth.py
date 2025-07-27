from flask import current_app, Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
import datetime

from app.models.user import User
from app.services.user_manager import UserManager
from app.services.token_manager import TokenManager
from app.utils.helpers import send_reset_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/signUp", methods=['GET', 'POST'])
def signup_page():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')
        role = request.form.get('role')

        if password != confirm_password:
            flash("Passwords do not match", "error")
            current_app.logger.warning(f"Password mismatch during signup for {email}")
            return redirect(url_for('auth.signup_page'))

        if UserManager.email_exists(email):
            flash("Email already registered", "error")
            current_app.logger.warning(f"Failed sign up attempt for email: {email} ({email} already exist) ")
            return redirect(url_for('auth.signup_page'))

        new_user = User(
            email=email,
            username=username,
            password_hash=generate_password_hash(password),
            role=role,
            created_at=datetime.datetime.now().isoformat()
        )

        UserManager.add_user(new_user)
        flash("Account created successfully! Please log in.", "success")
        current_app.logger.info(f"New {role} account created: {email}")
        return redirect(url_for('auth.login'))

    return render_template('signUp.html')


@auth_bp.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        email = request.form.get('email')
        password = request.form.get('password')

        user = UserManager.get_user(email)
        if not user or user.role != role or not user.verify_password(password):
            flash("Invalid credentials", "error")
            current_app.logger.warning(f"Failed login attempt for email: {email}")
            return redirect(url_for('auth.login'))

        session['user_email'] = email
        session['username'] = user.username
        session['role'] = user.role
        flash(f"Welcome back, {user.username}!", "success")
        current_app.logger.info(f"User {email} logged in successfully")
        return redirect(url_for('main.dashboard'))

    return render_template('login.html')


@auth_bp.route("/logout")
def logout():
    user_email = session.get('user_email', 'unknown')
    session.pop('user_email', None)
    session.pop('username', None)
    session.pop('role', None)
    current_app.logger.info(f"User {user_email} logged out successfully")
    return redirect(url_for('auth.login'))


@auth_bp.route("/forgot_password", methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')

        if not UserManager.email_exists(email):
            flash("No account with this email", "error")
            current_app.logger.warning(f"Password reset requested for non-existent email: {email}")
            return redirect(url_for('auth.login'))

        token = TokenManager.generate_token(email)
        if send_reset_email(email, token):
            flash("Password reset link sent", "success")
            current_app.logger.info(f"Password reset link has been sent to {email}")
        else:
            flash("Failed to send reset link", "error")
            current_app.logger.warning(f"Failed to send password reset link for email: {email}")

        return redirect(url_for('auth.login'))

    return render_template('forgot_password.html')


@auth_bp.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_password(token):
    valid, email = TokenManager.validate_token(token)
    if not valid:
        flash("Invalid or expired token", "error")
        current_app.logger.warning(f"Invalid/expired token used: {token}")
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        if password != confirm:
            flash("Passwords do not match", "error")
            return redirect(url_for('auth.reset_password', token=token))

        hashed = generate_password_hash(password)
        UserManager.update_user(email, password_hash=hashed)
        TokenManager.delete_token(token)
        flash("Password updated successfully!", "success")
        current_app.logger.info(f"Password for user {email} has changed successfully")
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', token=token)