import pytest

from app.core.config import settings
from app.core.exceptions import (
    DisposableEmailNotAllowedError,
    EmailDomainNotAllowedError,
)
from app.security.email_security import (
    validate_registration_email,
)


def test_normal_and_company_domains_allowed(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "email_domain_mode",
        "deny_disposable",
    )
    monkeypatch.setattr(
        settings,
        "block_disposable_emails",
        True,
    )

    assert (
        validate_registration_email(
            "person@gmail.com"
        )
        == "person@gmail.com"
    )

    assert (
        validate_registration_email(
            "employee@company.de"
        )
        == "employee@company.de"
    )


def test_disposable_domain_is_blocked(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "email_domain_mode",
        "deny_disposable",
    )
    monkeypatch.setattr(
        settings,
        "block_disposable_emails",
        True,
    )

    with pytest.raises(
        DisposableEmailNotAllowedError
    ):
        validate_registration_email(
            "person@mailinator.com"
        )


def test_company_allowlist_mode(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "email_domain_mode",
        "allowlist",
    )
    monkeypatch.setattr(
        settings,
        "allowed_email_domains",
        "company.com,company.de",
    )
    monkeypatch.setattr(
        settings,
        "block_disposable_emails",
        True,
    )

    assert (
        validate_registration_email(
            "employee@company.com"
        )
        == "employee@company.com"
    )

    with pytest.raises(
        EmailDomainNotAllowedError
    ):
        validate_registration_email(
            "someone@gmail.com"
        )
