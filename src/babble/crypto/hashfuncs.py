import hashlib

from Crypto.Hash import RIPEMD160


def sha256(contents: bytes) -> bytes:
    h = hashlib.sha256()
    h.update(contents)
    return h.digest()


def ripemd160(contents: bytes) -> bytes:
    h = RIPEMD160.new()
    h.update(contents)
    return h.digest()
