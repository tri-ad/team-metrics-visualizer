import datetime
import dateutil
import json
import logging
import os
from typing import Dict, List, Optional

from flask import current_app

from auth import auth
from common.exceptions import MissingConfigurationError
from jira import JIRA


def __oauth_dict() -> Dict:
    """
    Creates a dictionary with all information to perform authentication via OAuth.

    :return: OAuth-dictionary for JIRA.
    """
    access_token = auth.jira_token("jira_access_token")
    access_token_secret = auth.jira_token("jira_access_sec")
    rsa_key = auth.jira_rsa_key("jira_rsa_pem")

    if None in (access_token, access_token_secret, rsa_key):
        logging.warning(
            "Could not retrieve all necessary secrets for connecting to JIRA via OAuth."
        )

    return {
        "access_token": access_token,
        "access_token_secret": access_token_secret,
        "consumer_key": current_app.config["JIRA_CONSUMER_KEY"],
        # "consumer_secret": current_app.config["JIRA_CONSUMER_SECRET"],  # not yet needed
        "key_cert": rsa_key,
    }


def connect() -> Optional[JIRA]:
    """ Try to establish a connection to the JIRA API and return a JIRA-object on success.

    :raises MissingConfigurationError: Raises this error if the configuration is insufficient.
    :return: A `JIRA`-object to use for API-calls.
    :rtype: Optional[JIRA]
    """
    oauth_data = __oauth_dict()

    oauth_undefined_keys = [k for k, v in oauth_data.items() if v is None]

    if len(oauth_undefined_keys) > 0:
        raise MissingConfigurationError(
            f"The following JIRA variables are not configured: {oauth_undefined_keys}"
        )

    logging.debug("Connecting to JIRA.")
    try:
        jira = JIRA(server=current_app.config["JIRA_SERVER"], oauth=oauth_data,)
    except Exception as e:
        logging.error("Could not connect to JIRA. The error was {}.".format(e))
        return None
    else:
        return jira
