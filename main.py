from typing_extensions import TypedDict
from typing import Optional
from langgraph.graph import StateGraph, START, END
from structured_output import Reply, structured_llm
from tools import type_print, type_command

# Graph state
class State(TypedDict):
    user_query: str
    reply: Reply

# Nodes
def llm_node(state: State):
    output = structured_llm.invoke(state["user_query"])
    return {"reply": output}

def terminal_command_node(state: State):
    type_command(state["reply"].command)
    return {}

def llm_answer_node(state: State):
    type_print(state["reply"].answer)
    return {}

# Router
def router(state: State):
    return "terminal_command_node" if state["reply"].command is not None else "llm_answer_node"

# Build workflow
workflow = StateGraph(State)

workflow.add_node("llm_node", llm_node)
workflow.add_node("terminal_command_node", terminal_command_node)
workflow.add_node("llm_answer_node", llm_answer_node)

workflow.add_edge(START, "llm_node")
workflow.add_conditional_edges("llm_node", router, {
    "terminal_command_node": "terminal_command_node",
    "llm_answer_node": "llm_answer_node",
})
workflow.add_edge("terminal_command_node", END)
workflow.add_edge("llm_answer_node", END)

chain = workflow.compile()

if __name__ == "__main__":
    import sys
    user_query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("Enter your query: ")
    chain.invoke({"user_query": user_query})
