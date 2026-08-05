from __future__ import annotations

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class MfaEnrollmentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    secret: str
    provisioning_uri: str


class MfaVerificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(
        min_length=6,
        max_length=8,
        pattern=r"^[0-9]+$",
    )


class MfaRecoveryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recovery_codes: list[str]


class MfaDisableRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=6, max_length=32)


class MfaLoginChallenge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    challenge_token: str
    mfa_required: bool = True


class MfaLoginVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    challenge_token: str = Field(min_length=20)
    code: str = Field(min_length=6, max_length=32)
