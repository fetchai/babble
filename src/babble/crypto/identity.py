import base64
import hashlib
import json
import os
from typing import Tuple

import bech32
import ecdsa
from ecdsa.util import sigencode_string_canonize
from ecies import PrivateKey, decrypt, encrypt

from .hashfuncs import ripemd160, sha256


def _to_bech32(prefix: str, data: bytes) -> str:
    data_base5 = bech32.convertbits(data, 8, 5, True)
    if data_base5 is None:
        raise RuntimeError("Unable to parse address")  # pragma: no cover
    return bech32.bech32_encode(prefix, data_base5)


def _compute_address(sk: ecdsa.SigningKey) -> Tuple[str, str]:
    public_key = sk.get_verifying_key().to_string("compressed")
    raw_address = ripemd160(sha256(public_key))
    return _to_bech32("fetch", raw_address), public_key.hex()


class Identity:
    @staticmethod
    def from_seed(text: str) -> "Identity":
        private_key_bytes = sha256(sha256(text.encode()))
        return Identity(private_key_bytes)

    @staticmethod
    def generate() -> "Identity":
        return Identity(os.urandom(32))

    def __init__(self, private_key: bytes):
        # build the keys
        self._sk = ecdsa.SigningKey.from_string(
            private_key, curve=ecdsa.SECP256k1, hashfunc=hashlib.sha256
        )
        self._msg_key = PrivateKey(private_key)

        # compute the derived pieces of the identity
        address, public_key = _compute_address(self._sk)
        self._address = address
        self._public_key = public_key

    @property
    def address(self) -> str:
        return self._address

    @property
    def public_key(self) -> str:
        return self._public_key

    def sign_arbitrary(self, data: bytes) -> Tuple[str, str]:
        # create the sign doc
        sign_doc = {
            "chain_id": "",
            "account_number": "0",
            "sequence": "0",
            "fee": {
                "gas": "0",
                "amount": [],
            },
            "msgs": [
                {
                    "type": "sign/MsgSignData",
                    "value": {
                        "signer": self.address,
                        "data": base64.b64encode(data).decode(),
                    },
                },
            ],
            "memo": "",
        }

        raw_sign_doc = json.dumps(
            sign_doc, sort_keys=True, separators=(",", ":")
        ).encode()
        signature = self.sign(raw_sign_doc)
        enc_sign_doc = base64.b64encode(raw_sign_doc).decode()

        return enc_sign_doc, signature

    def sign(self, data: bytes) -> str:
        raw_signature = bytes(self._sk.sign(data, sigencode=sigencode_string_canonize))
        return base64.b64encode(raw_signature).decode()

    @staticmethod
    def encrypt_message(target: str, data: bytes) -> bytes:
        return encrypt(target, data)

    def decrypt_message(self, data: bytes) -> bytes:
        return decrypt(self._msg_key.secret, data)
