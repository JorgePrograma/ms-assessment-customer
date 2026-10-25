"""Business invariants of a customer, enforced for every entry point (HTTP, scripts, future consumers).

The HTTP layer validates the request shape first; this guarantees the rules even without it.
"""

import re

from app.domain.errors import ValidationError

NAME_MAX_LENGTH = 120
EMAIL_MAX_LENGTH = 320
_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class CustomerValidator:
    @staticmethod
    def validate_new(name: str, email: str) -> None:
        name, email = name.strip(), email.strip()
        if not name:
            raise ValidationError("name is required", field="name")
        if len(name) > NAME_MAX_LENGTH:
            raise ValidationError(f"name must be at most {NAME_MAX_LENGTH} characters", field="name")
        if not email:
            raise ValidationError("email is required", field="email")
        if len(email) > EMAIL_MAX_LENGTH or not _EMAIL_PATTERN.match(email):
            raise ValidationError("email is not a valid email address", field="email")
