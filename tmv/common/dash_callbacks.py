from dash.dependencies import Output, Input
from flask_security import current_user
from dash_layout import USER_GREETING_ID


_callbacks = []


def register_callback(*args, **kwargs):
    def inner(f):
        _callbacks.append((f, args, kwargs))
        return f

    return inner


def register_common_callbacks(dash_app):
    for (f, args, kwargs) in _callbacks:
        dash_app.callback(*args, **kwargs)(f)


@register_callback(
    Output(USER_GREETING_ID, "children"), [Input(USER_GREETING_ID, "id")],
)
def _callback_current_user(_):
    try:
        return f"Hi {current_user.first_name} 👋"
    except AttributeError:
        return "Hi! 👋"
