from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Tuple

import jwt
import requests

from .config import AUTH_SERVER
from .crypto.identity import Identity


@dataclass
class TokenMetadata:
    address: str
    public_key: str
    issued_at: datetime
    expires_at: datetime


def authenticate(identity: Identity) -> Tuple[str, TokenMetadata]:
    r = requests.post(
        f"{AUTH_SERVER}/request_token",
        json={
            "address": identity.address,
            "public_key": identity.public_key,
        },
    )
    r.raise_for_status()

    payload = r.json()["payload"]

    # create the signature
    signed_bytes, signature = identity.sign_arbitrary(payload.encode())

    r = requests.post(
        f"{AUTH_SERVER}/login",
        json={
            "public_key": identity.public_key,
            "signed_bytes": signed_bytes,
            "signature": signature,
        },
    )
    r.raise_for_status()

    # extract the token
    token = str(r.json()["token"])

    # parse the token
    token_data = jwt.decode(
        token, algorithms=["RS*"], options={"verify_signature": False}
    )

    # build the token metadata
    metadata = TokenMetadata(
        address=str(token_data["name"]),
        public_key=str(token_data["pubkey"]),
        issued_at=datetime.fromtimestamp(token_data["iat"], timezone.utc),
        expires_at=datetime.fromtimestamp(token_data["exp"], timezone.utc),
    )

    assert metadata.address == identity.address
    assert metadata.public_key == identity.public_key

    return token, metadata
