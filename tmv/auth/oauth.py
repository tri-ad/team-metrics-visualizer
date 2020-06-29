from functools import wraps
from flask import current_app, abort


def require_oauth_config(name):
    def inner(f):
        @wraps(f)
        def wrapper(*args, **kwds):
            try:
                getattr(current_app.oauth, name)
            except AttributeError:
                return abort(404)
            return f(*args, **kwds)

        return wrapper

    return inner
