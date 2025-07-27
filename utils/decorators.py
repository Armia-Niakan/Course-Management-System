from functools import wraps
from flask import session, flash, redirect, url_for, current_app, request

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            flash("Unauthorized - Admin access required", "error")
            current_app.logger.warning(f"Unauthorized admin access attempt by {session.get('user_email', 'unknown')}")
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'teacher':
            flash("Unauthorized - Teacher access required", "error")
            current_app.logger.warning(
                f"Unauthorized teacher access attempt by {session.get('user_email', 'unknown')}")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash("Please login to access this page", "error")
            current_app.logger.warning(
                f"Unauthorized access attempt from IP: {request.remote_addr}")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function