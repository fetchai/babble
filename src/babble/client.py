from datetime import datetime, timedelta, timezone
from typing import List

import bech32
from pydantic import BaseModel

from .auth import authenticate
from .crypto.exceptions import RoutingError
from .crypto.identity import Identity
from .encoding import from_base64, from_json, to_base64, to_json
from .mailbox import (
    dispatch_messages,
    list_messages,
    lookup_messaging_public_key,
    register_messaging_public_key,
)

EXPIRATION_BUFFER_SECONDS = 60 * 5  # 5 minutes


def _validate_address(address: str):
    hrp, _ = bech32.bech32_decode(address)
    if hrp is None or hrp not in ("fetch", "agent"):
        raise ValueError(f"Bad delegate address {address}")


class Message(BaseModel):
    id: str
    sender: str
    target: str
    text: str
    sent_at: datetime
    expires_at: datetime


class Client:
    def __init__(
        self,
        delegate_address: str,
        delegate_pubkey: str,
        signature: str,
        signed_obj_base64: str,
        identity: Identity,
        chain_id: str,
        name: str = None,
    ):
        _validate_address(delegate_address)

        # identity and delegation
        self._delegate_address = str(delegate_address)
        self._delegate_pubkey = delegate_pubkey
        self._signature = signature
        self._signed_obj_base64 = signed_obj_base64
        self._identity = identity
        self._chain_id = chain_id
        self._name = name

        # build and restore the delivered set
        self._last_rx_timestamp = self._now()

        # authenticate against the API
        self._token = None
        self._token_metadata = {"expires_at": self._now()}
        self._update_authentication()

        # ensure the registration is in place
        self._update_registration()

    def _update_authentication(self):
        if (
            self._token is None
            or self._token_metadata.expires_at
            < self._now() - timedelta(seconds=EXPIRATION_BUFFER_SECONDS)
        ):
            self._token, self._token_metadata = authenticate(self._identity, self._name)
            if not self._token or not self._token_metadata:
                raise ValueError("Failed to authenticate")

    def __repr__(self):
        return f"{self._delegate_address}  ({self._identity.public_key})"

    @property
    def delegate_address(self) -> str:
        return self._delegate_address

    def send(self, target_address: str, message: str, msg_type: int = 1):
        self._update_authentication()

        target_public_key = lookup_messaging_public_key(
            self._token, target_address, self._chain_id
        )
        if target_public_key is None:
            raise RoutingError(f"Unable to route to {target_address}")

        # build up the message structure
        now = self._now().isoformat()
        message = {
            "sender": self._identity.public_key,  # public key (hex)
            "target": target_public_key,  # public key (hex)
            "groupLastSeenTimestamp": now,
            "lastSeenTimestamp": now,
            "type": msg_type,  # 1 for text message, 2 for transaction data
            "content": {
                "text": message,
            },
        }

        raw_message = to_json(message).encode()

        # encrypt each part?
        sender_cipher = Identity.encrypt_message(self._identity.public_key, raw_message)
        target_cipher = Identity.encrypt_message(target_public_key, raw_message)

        # JSON + Base64
        payload = to_json(
            {
                "encryptedSenderData": to_base64(sender_cipher),
                "encryptedTargetData": to_base64(target_cipher),
            }
        ).encode()

        # create the signature
        signature = self._identity.sign(payload)

        envelope = {
            "data": to_base64(payload),
            "senderPublicKey": self._identity.public_key,
            "targetPublicKey": target_public_key,
            "groupLastSeenTimestamp": now,
            "lastSeenTimestamp": now,
            "signature": signature,
            "channelId": "MESSAGING",
        }

        # encode and dispatch the envelope
        enc_envelope = to_base64(to_json(envelope))
        dispatch_messages(self._token, [enc_envelope])

    def receive(self) -> List[Message]:
        self._update_authentication()

        output = []

        latest_rx_timestamp = self._last_rx_timestamp

        # attempt to decode the messages
        for raw_message in list_messages(self._token):
            if raw_message.target != self.delegate_address:
                continue

            # only retrieve new messages
            if raw_message.sent_at <= self._last_rx_timestamp:
                continue

            latest_rx_timestamp = max(latest_rx_timestamp, raw_message.sent_at)

            envelope = from_json(from_base64(raw_message.contents))
            payload = from_json(from_base64(envelope["data"]))
            encrypted_message = from_base64(payload["encryptedTargetData"])
            message = from_json(self._identity.decrypt_message(encrypted_message))

            output.append(
                Message(
                    id=raw_message.id,
                    sender=raw_message.sender,
                    target=raw_message.target,
                    text=message["content"]["text"],
                    sent_at=raw_message.sent_at,
                    expires_at=raw_message.expires_at,
                )
            )

        # update the timestamp filter
        self._last_rx_timestamp = latest_rx_timestamp

        # drop the received messages from the mailbox (not currently supported)
        # drop_messages(self._token, received_msgs)

        return output

    def _update_registration(self):
        registered_pub_key = lookup_messaging_public_key(
            self._token, self._delegate_address, self._chain_id
        )
        if registered_pub_key != self._identity.public_key:
            print(
                f"Registering {self._delegate_address} to {self._identity.address}..."
            )
            register_messaging_public_key(
                self._token,
                self._delegate_address,
                self._identity.public_key,
                self._delegate_pubkey,
                self._signature,
                self._signed_obj_base64,
                self._chain_id,
            )
            print(
                f"Registering {self._delegate_address} to {self._identity.address}...complete"
            )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(tz=timezone.utc)
