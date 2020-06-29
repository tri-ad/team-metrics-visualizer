import pytest
from auth import secrets

mock_config = {
    "JIRA_OAUTH_LOC": "ENV",
    "TEST_SECRET": "test",
    "TEST_RSA_KEY": "-----BEGIN RSA PRIVATE KEY----- test -----END RSA PRIVATE KEY-----",
}


def test_CanRetrieveJIRATokenFromEnv(app, monkeypatch):
    monkeypatch.setattr(secrets.current_app, "config", mock_config)
    assert secrets.jira_token("TEST_SECRET") == "test"


def test_CorrectlyFormatsJIRARSAKey(app, monkeypatch):
    monkeypatch.setattr(secrets.current_app, "config", mock_config)
    assert (
        secrets.jira_rsa_key("TEST_RSA_KEY")
        == "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----"
    )
