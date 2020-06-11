import logging
from typing import Optional
import boto3.session
import json
import base64
from botocore.exceptions import ClientError
from flask import current_app


def get_secret(secret_name: str) -> Optional[str]:
    """
    Retrieve secret with name 'secret_name' from AWS Secrets Manager.

    :param secret_name: Name of the secret to retrieve.
    :return: The secret.
    """

    AWS_REGION = current_app.config["AWS_REGION"]

    # Create a session with the Secrets Manager
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=AWS_REGION)

    # Try to retrieve the secret from AWS Secrets Manager
    try:
        secret_value = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        logging.error(f"AWS error: {e}. (Region={AWS_REGION}).")
        return None
    else:
        # Decrypts secret using the associated KMS CMK.
        if "SecretString" in secret_value:
            return json.loads(secret_value["SecretString"])[secret_name]
        else:
            return base64.b64decode(secret_value["SecretBinary"])
