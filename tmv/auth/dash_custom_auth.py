from dash_auth.auth import Auth
from flask_security import current_user, login_required
from flask import current_app


class DashFlaskSecurityAuth(Auth):
    def _protect_views(self):
        # original version tries to protect non-dash views too, so we redefine it
        # to protect only dash views

        for view_name, view_method in self.app.server.view_functions.items():
            is_dash_index = view_name == self._index_view_name  # protected separately
            if is_dash_index:
                continue

            is_dash_page = view_name.startswith(self._index_view_name)  # /dash/*

            if not is_dash_page:
                continue

            self.app.server.view_functions[view_name] = self.auth_wrapper(view_method)

    def is_authorized(self):
        return current_user.is_authenticated

    def auth_wrapper(self, f):
        return login_required(f)

    def index_auth_wrapper(self, original_index):
        return self.auth_wrapper(original_index)

    def login_request(self):
        return current_app.login_manager.unauthorized()
