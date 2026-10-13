"""User-approved facts for later chats. No automatic extraction."""
import json
import re
from sqlalchemy import select
from . import db


class MemoryRejected(ValueError):
    pass


SENSITIVE = re.compile(r'\b(?:password|passphrase|api[ -]?key|secret[ -]?key|private[ -]?key|cvv|cvc|card[ -]?number|bank[ -]?account)\b', re.I)
CARD_LIKE = re.compile(r'(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)')


def clean(label: str, content: str) -> tuple[str, str]:
    label, content = label.strip(), content.strip()
    if not label or not content:
        raise MemoryRejected('A label and memory are required.')
    if SENSITIVE.search(label + ' ' + content) or CARD_LIKE.search(content):
        raise MemoryRejected('Do not save credentials, bank or card details as memory.')
    return label, content


def view(row: db.Memory) -> dict:
    return {'id': row.id, 'label': row.label, 'content': row.content,
            'origin': row.origin, 'created': row.created, 'updated': row.updated}


def chat_context(session, user_id: str) -> str:
    rows = session.scalars(select(db.Memory).where(db.Memory.user_id == user_id)
        .order_by(db.Memory.updated.desc(), db.Memory.id.desc()).limit(50)).all()
    selected = []
    remaining = 4000
    for row in rows:
        item = {'label': row.label, 'content': row.content}
        serialized = json.dumps(item, ensure_ascii=False)
        if len(serialized) > remaining:
            continue
        selected.append(item)
        remaining -= len(serialized)
    return json.dumps(selected, ensure_ascii=False)

