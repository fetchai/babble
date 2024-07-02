import base64
import json
from typing import Any, Union


def to_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def from_json(data: Union[bytes, str]) -> Any:
    return json.loads(data)


def to_base64(data: Union[bytes, str]) -> str:
    if isinstance(data, str):
        data = data.encode()
    return base64.b64encode(data).decode()


def from_base64(data: str) -> bytes:
    return base64.b64decode(data)
