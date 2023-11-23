from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Tuple

import jwt
import requests

from .config import AUTH_SERVER
from .crypto.identity import Identity
from .encoding import to_base64, from_base64


@dataclass
class TokenMetadata:
    address: str
    public_key: str
    issued_at: datetime
    expires_at: datetime


def authenticate(identity: Identity, name: str = None) -> Tuple[str, TokenMetadata]:
    r = requests.post(
        f"{AUTH_SERVER}/auth/login/wallet/challenge",
        json={
            "address": identity.address,
            "client_id": name if name else "uagent",
        },
    )
    r.raise_for_status()
    resp = r.json()

    payload = resp["challenge"]

    # create the signature
    _, signature = identity.sign_arbitrary(payload.encode())

    login_request = {
        "address": identity.address,
        "public_key": {
            "value": to_base64(bytes.fromhex(identity.public_key)),
            "type": "tendermint/PubKeySecp256k1",
        },
        "nonce": resp["nonce"],
        "challenge": resp["challenge"],
        "signature": signature,
        "client_id": name if name else "uagent",
        "scope": "",
    }

    r = requests.post(
        f"{AUTH_SERVER}/auth/login/wallet/verify",
        json=login_request,
    )
    r.raise_for_status()

    r = requests.post(
        f"{AUTH_SERVER}/tokens",
        json=r.json(),
    )
    r.raise_for_status()

    # extract the token
    token = str(r.json()["access_token"])

    # parse the token
    token_data = jwt.decode(
        token,
        algorithms=["RS*"],
        options={"verify_signature": False},
        issuer="fetch.ai",
    )

    # build the token metadata
    metadata = TokenMetadata(
        address=identity.address,
        public_key=from_base64(str(token_data["pk"])).hex(),
        issued_at=datetime.fromtimestamp(token_data["iat"], timezone.utc),
        expires_at=datetime.fromtimestamp(token_data["exp"], timezone.utc),
    )

    assert metadata.address == identity.address
    assert metadata.public_key == identity.public_key

    return token, metadata
