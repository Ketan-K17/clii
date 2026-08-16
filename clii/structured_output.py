from clii.chat_model import llm

from pydantic import BaseModel, Field, model_validator
from typing import Optional


class Reply(BaseModel):
    command: Optional[str] = Field(None, description="Terminal command to execute. Set this when the user asks to perform an action that can be fulfilled by running a shell command.")
    answer: Optional[str] = Field(None, description="Natural language answer. Set this when the user asks a question.")

    @model_validator(mode='after')
    def exactly_one(self) -> 'Reply':
        if not self.command:
            self.command = None
        if not self.answer:
            self.answer = None
        if (self.command is None) == (self.answer is None):
            raise ValueError("Exactly one of 'command' or 'answer' must be set, not both or neither.")
        return self


SYSTEM_PROMPT = (
    "You are clii, a terminal assistant on macOS. You MUST respond by calling "
    "the Reply tool, never with plain text.\n"
    "- If the user asks you to do something that a shell command can accomplish, "
    "set `command` to that single shell command. No markdown fences, no "
    "explanation, no alternatives — the string is typed straight into the "
    "user's prompt.\n"
    "- Otherwise set `answer` to a plain-language response.\n"
    "Set exactly one of the two, never both."
)


def _prepend_system(messages):
    """Give the model the command-vs-answer contract explicitly.

    Without this, models infer it from the Reply field descriptions alone, and
    weaker ones get it wrong: minimax answers a `kubectl` request with a prose
    walkthrough instead of calling the tool. Azure/OpenAI happen to cope, but
    the prompt costs them nothing.
    """
    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]
    return [{"role": "system", "content": SYSTEM_PROMPT}, *messages]


# Augment the LLM with schema for structured output.
#
# include_raw=True because local/Ollama models don't honour tool_choice the way
# Azure and OpenAI do: some answer in plain content with no tool call at all,
# others call the tool but set both fields. Either way the plain parser yields
# None and every caller downstream blows up on `reply.command`, so we keep the
# raw message around and salvage a Reply from it.
_structured_llm = llm.with_structured_output(
    Reply, method="function_calling", include_raw=True
)


def _coerce_reply(result: dict) -> Reply:
    parsed = result.get("parsed")
    if isinstance(parsed, Reply):
        return parsed

    raw = result.get("raw")

    # Tool call present but rejected by the validator — usually both fields
    # set. A command is the more specific intent, so it wins.
    for tool_call in getattr(raw, "tool_calls", None) or []:
        args = tool_call.get("args") or {}
        command = (args.get("command") or "").strip()
        answer = (args.get("answer") or "").strip()
        if command:
            return Reply(command=command)
        if answer:
            return Reply(answer=answer)

    # No tool call at all: the model just replied in prose.
    content = (getattr(raw, "content", "") or "").strip()
    if content:
        return Reply(answer=content)

    error = result.get("parsing_error")
    return Reply(
        answer=f"The model returned an unusable response ({error})."
        if error
        else "The model returned an empty response."
    )


structured_llm = _prepend_system | _structured_llm | _coerce_reply

if __name__ == "__main__":
    output = structured_llm.invoke("look for the keyword 'sanity' in my command history")
    print(output)
