from datetime import datetime

from flask import Blueprint, redirect, current_app, url_for, abort, flash, request
from flask_security import login_user

from database import db
from structure.auth import User, UserExternalService, UserExternalServiceEnum
from common.utils import require_oauth_config


user = Blueprint("user", __name__)


@user.route("/")
def index():
    return redirect("/dash/")


@user.route("/okta-login")
@require_oauth_config("okta")
def okta_login():
    redirect_uri = url_for("user.okta_authorize", _external=True)
    return current_app.oauth.okta.authorize_redirect(redirect_uri)


@user.route("/okta-callback")
@require_oauth_config("okta")
def okta_authorize():
    error = request.args.get("error")
    if error:
        flash("Could not log in via Okta", "error")
        return redirect(url_for("security.login"))

    token = current_app.oauth.okta.authorize_access_token()
    user_info = current_app.oauth.okta.userinfo()

    ext_service = UserExternalService.query.filter_by(
        service=UserExternalServiceEnum.okta.value, service_user_id=user_info["sub"]
    ).first()

    if ext_service:
        ext_service.auth_info = token
        ext_service.user_info = user_info
        ext_service.last_used_at = datetime.utcnow()
        db.session.commit()
    else:
        # we assume okta's emails are unique, but it's not enforced
        user = User(
            email=user_info["email"],
            first_name=user_info.get("given_name", ""),
            last_name=user_info.get("family_name", ""),
        )
        db.session.add(user)

        ext_service = UserExternalService(
            user=user,
            service=UserExternalServiceEnum.okta.value,
            service_user_id=user_info["sub"],
            auth_info=token,
            user_info=user_info,
        )
        db.session.add(ext_service)
        db.session.commit()

    login_user(ext_service.user)
    current_app.security.datastore.commit()

    return redirect("/")
