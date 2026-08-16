"""Cross-invocation conversation memory.

clii exits after every command it emits (interactive REPL included), so
without this a follow-up correction like "no, only top-level ones" has
nothing to refer back to once the process is gone. We persist the last
conversation to disk and reload it on the next invocation, as long as it's
still fresh enough to plausibly be "the same task."
"""

import json
import os
import time

from langchain_core.messages import AIMessage, HumanMessage

SESSION_PATH = os.path.expanduser("~/.config/clii/session.json")

# How long a session stays resumable after its last turn. Long enough to
# cover "wait, tweak that" a minute later, short enough that an unrelated
# query tomorrow doesn't drag in yesterday's context.
SESSION_TTL_SECONDS = 15 * 60


def load_session() -> list:
    """Return the saved message history, or [] if there isn't one / it's stale."""
    try:
        with open(SESSION_PATH) as f:
            data = json.load(f)
    except (FileNotFoundError, ValueError):
        return []

    if time.time() - data.get("timestamp", 0) > SESSION_TTL_SECONDS:
        return []

    return _parse_messages(data.get("messages", []))


def load_all_messages() -> list:
    """Return the saved message history regardless of staleness.

    Used by `clii history`, where the point is to let you look at (and edit)
    whatever's on disk even if it's aged out of automatic reuse.
    """
    try:
        with open(SESSION_PATH) as f:
            data = json.load(f)
    except (FileNotFoundError, ValueError):
        return []
    return _parse_messages(data.get("messages", []))


def _parse_messages(entries: list) -> list:
    messages = []
    for entry in entries:
        role, content = entry.get("role"), entry.get("content", "")
        if role == "human":
            messages.append(HumanMessage(content=content))
        elif role == "ai":
            messages.append(AIMessage(content=content))
    return messages


def save_session(messages: list) -> None:
    os.makedirs(os.path.dirname(SESSION_PATH), exist_ok=True)
    serialised = [
        {
            "role": "human" if isinstance(m, HumanMessage) else "ai",
            "content": m.content,
        }
        for m in messages
    ]
    with open(SESSION_PATH, "w") as f:
        json.dump({"timestamp": time.time(), "messages": serialised}, f)


def clear_session() -> None:
    try:
        os.remove(SESSION_PATH)
    except FileNotFoundError:
        pass
