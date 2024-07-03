from datetime import datetime, timezone
from typing import Optional, Tuple

import jwt
import requests
from pydantic import BaseModel

from .config import AUTH_SERVER, DEFAULT_REQUEST_TIMEOUT
from .crypto.identity import Identity
from .encoding import from_base64, to_base64


class TokenMetadata(BaseModel):
    address: str
    public_key: str
    issued_at: datetime
    expires_at: datetime


def send_post_request(url: str, data: dict) -> Optional[dict]:
    """Send a POST request to the given URL with the given data."""
    try:
        response = requests.post(url, json=data, timeout=DEFAULT_REQUEST_TIMEOUT)
        return response.json()
    except requests.exceptions.RequestException as err:
        print(f"Error: {err}")
        return None


def authenticate(identity: Identity, name: str = None) -> Tuple[str, TokenMetadata]:
    """Authenticate the given identity and return the token and metadata."""
    resp = send_post_request(
        f"{AUTH_SERVER}/auth/login/wallet/challenge",
        {
            "address": identity.address,
            "client_id": name if name else "uagent",
        },
    )
    if not resp or "challenge" not in resp or "nonce" not in resp:
        return None, None

    payload: str = resp["challenge"]

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

    login_resp = send_post_request(
        f"{AUTH_SERVER}/auth/login/wallet/verify", login_request
    )
    if not login_resp:
        return None, None

    token_resp = send_post_request(f"{AUTH_SERVER}/tokens", login_resp)
    if not token_resp or "access_token" not in token_resp:
        return None, None

    # extract the token
    token = str(token_resp["access_token"])

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

    if (
        not metadata.address == identity.address
        or not metadata.public_key == identity.public_key
    ):
        return None, None

    return token, metadata
