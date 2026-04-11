from clii.chat_model import llm

from pydantic import BaseModel, Field, model_validator
from typing import Optional


class Reply(BaseModel):
    command: Optional[str] = Field(None, description="Terminal command to execute. Set this when the user asks to do something.")
    answer: Optional[str] = Field(None, description="Natural language answer. Set this when the user asks a question.")

    @model_validator(mode='after')
    def exactly_one(self) -> 'Reply':
        if (self.command is None) == (self.answer is None):
            raise ValueError("Exactly one of 'command' or 'answer' must be set, not both or neither.")
        return self


# Augment the LLM with schema for structured output
structured_llm = llm.with_structured_output(Reply, method="function_calling")

if __name__ == "__main__":
    output = structured_llm.invoke("look for the keyword 'sanity' in my command history")
    print(output)
