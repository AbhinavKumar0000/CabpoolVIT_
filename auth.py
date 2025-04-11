from flask import session, redirect, url_for, flash, request
from functools import wraps

# Helper function to check if user is logged in
def is_authenticated():
    return 'user_id' in session and session.get('user_id') is not None

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            flash('Please log in to access this page', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function
