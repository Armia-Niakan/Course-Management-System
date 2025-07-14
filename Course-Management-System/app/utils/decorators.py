from functools import wraps
from flask import session, flash, redirect, url_for, current_app


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            flash("Unauthorized - Admin access required", "error")
            current_app.logger.warning(f"Unauthorized admin access attempt by {session.get('user_email', 'unknown')}")
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function
