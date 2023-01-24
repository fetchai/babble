from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

import requests

from .config import MEMORANDUM_SERVER


def _from_js_date(value: int) -> datetime:
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)


def _execute(query: str, *, token: str, variables: Optional[Dict[str, Any]] = None):
    payload = {
        'query': query,
        'variables': variables
    }

    # make the request
    r = requests.post(f'{MEMORANDUM_SERVER}/graphql', json=payload, headers={
        'authorization': f'bearer {token}',
    })
    r.raise_for_status()

    return r.json()


def lookup_messaging_public_key(token: str, address: str) -> Optional[str]:
    resp = _execute("""
    query Query($address: String!) {
      publicKey(address: $address, channelId: MESSAGING) {
        publicKey
      }
    }
    """, variables={'address': address}, token=token)

    data = resp['data']['publicKey']
    if data is None:
        return None

    return data['publicKey']


def register_messaging_public_key(token: str, address: str, public_key: str):
    variables = {
        'publicKeyDetails': {
            'publicKey': public_key,
            'address': address,
            'channelId': 'MESSAGING',
            'privacySetting': 'EVERYBODY',
            'readReceipt': False,
        }
    }

    _execute("""
    mutation Mutation($publicKeyDetails: InputPublicKey!) {
      updatePublicKey(publicKeyDetails: $publicKeyDetails) {
        publicKey
        privacySetting
        readReceipt
      }
    }
    """, variables=variables, token=token)


def dispatch_messages(token: str, messages: List[str]):
    variables = {
        'messages': list(
            map(
                lambda x: {'contents': x},
                messages,
            )
        )
    }

    _execute("""
    mutation Mutation($messages: [InputMessage!]!) {
      dispatchMessages(messages: $messages) {
        id
        sender
        target
        contents
        expiryTimestamp
        commitTimestamp
      }
    }
    """, variables=variables, token=token)


@dataclass
class RawMessage:
    id: str
    group_id: str
    sender: str
    target: str
    contents: str
    sent_at: datetime
    expires_at: datetime


def list_messages(token: str) -> List[RawMessage]:
    resp = _execute("""
    query Messages {
      mailbox {
        messages {
          id
          groupId
          expiryTimestamp
          contents
          commitTimestamp
          sender
          target
        }
      }
    }
    """, token=token)

    def extract_message(data) -> RawMessage:
        return RawMessage(
            id=data['id'],
            group_id=data['groupId'],
            sender=data['sender'],
            target=data['target'],
            contents=data['contents'],
            sent_at=_from_js_date(data['commitTimestamp']),
            expires_at=_from_js_date(data['expiryTimestamp']),
        )

    messages = list(
        map(
            extract_message,
            resp['data']['mailbox']['messages'],
        )
    )

    return messages


def drop_messages(token: str, ids: List[str]):
    # no-op if the list is empty
    if len(ids) == 0:
        return

    variables = {
        'ids': ids,
    }

    resp = _execute("""
    mutation Mutation($ids: [ID!]!) {
      dropMessages(ids: $ids) {
        id
      }
    }
    """, variables=variables, token=token)
