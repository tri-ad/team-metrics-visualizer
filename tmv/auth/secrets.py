import logging
import os
from enum import Enum, auto
from aws import secretsManager
from flask import current_app
from typing import Optional


class SecretSource(Enum):
    Env = "ENV"
    Aws = "AWS"


def jira_token(token_name: str) -> Optional[str]:
    try:
        return _token(token_name, SecretSource(current_app.config["JIRA_OAUTH_LOC"]))
    except ValueError:
        allowed_values = ", ".join([member.value for member in SecretSource])
        logging.error(
            f"Please configure JIRA_OAUTH_LOC to take one of these values: {allowed_values}. "
            f"Defaulting to ENV."
        )
        return _token(token_name, SecretSource.Env)


def jira_rsa_key(key_name: str) -> Optional[str]:
    try:
        return _rsa_key(key_name, SecretSource(current_app.config["JIRA_OAUTH_LOC"]))
    except ValueError:
        allowed_values = ", ".join([member.value for member in SecretSource])
        logging.error(
            f"Please configure JIRA_OAUTH_LOC to take one of these values: {allowed_values}. "
            f"Defaulting to ENV."
        )
        return _rsa_key(key_name, SecretSource.Env)


def _token(token_name: str, source: SecretSource) -> Optional[str]:
    """
    Retrieves a token, either from local storage or using AWS.

    :param token_name: The name of the token to retrieve.
    :return: The token.
    """
    if source == SecretSource.Aws:
        return secretsManager.get_secret(token_name)
    elif source == SecretSource.Env:
        return current_app.config[token_name.upper()]
    else:
        return None


def _rsa_key(key_name: str, source: SecretSource) -> Optional[str]:
    """
    Returns a correctly formatted RSA-key with name `key_name` from AWS or local.

    :param key_name: The name of the RSA-key.
    :return: The RSA-key
    """
    key_raw = None
    if source == SecretSource.Aws:
        # Retrieve RSA-key. This key will not have newlines after preamble and therefore
        #   fail to decode.
        key_raw = secretsManager.get_secret(key_name)
    elif source == SecretSource.Env:
        key_raw = current_app.config[key_name.upper()]
    # Return RSA-key with correct newlines inserted.
    if key_raw:
        return key_raw.replace(
            "-----BEGIN RSA PRIVATE KEY----- ", "-----BEGIN RSA PRIVATE KEY-----\n"
        ).replace(" -----END RSA PRIVATE KEY-----", "\n-----END RSA PRIVATE KEY-----")
    return None
