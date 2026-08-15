import argparse
import os
import sys
import warnings

warnings.filterwarnings(
    "ignore",
    message="Core Pydantic V1 functionality isn't compatible",
    category=UserWarning,
)

CONFIG_PATH = os.path.expanduser("~/.config/clii/.env")

AZURE_CONFIG_KEYS = [
    ("AZURE_OPENAI_CHAT_ENDPOINT", "Azure OpenAI Endpoint"),
    ("AZURE_OPENAI_CHAT_KEY", "Azure OpenAI Key"),
    ("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "Deployment Name"),
    ("AZURE_OPENAI_CHAT_MODEL", "Model Name"),
    ("AZURE_API_VERSION", "API Version"),
    ("LLM_TEMPERATURE", "Temperature (e.g. 0)"),
]

OLLAMA_CONFIG_KEYS = [
    ("OLLAMA_MODEL", "Ollama Model (e.g. llama3.2)"),
    ("OLLAMA_BASE_URL", "Ollama Base URL (e.g. http://localhost:11434)"),
    ("LLM_TEMPERATURE", "Temperature (e.g. 0)"),
]


PROVIDERS = [
    ("azure", "AzureChatOpenai", AZURE_CONFIG_KEYS),
    ("ollama", "Ollama", OLLAMA_CONFIG_KEYS),
]


def configure():
    from clii.tools import select_menu

    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    choice = select_menu(
        "Please select your model provider",
        [label for _, label, _ in PROVIDERS],
    )
    provider, _, config_keys = PROVIDERS[choice]
    print("Configuring clii — credentials will be saved to", CONFIG_PATH)
    lines = [f"LLM_PROVIDER={provider}"]
    for key, label in config_keys:
        value = input(f"{label}: ").strip()
        lines.append(f"{key}={value}")
    with open(CONFIG_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Config saved to {CONFIG_PATH}")


def _check_config():
    if not os.path.exists(CONFIG_PATH):
        print("No config found. Run `clii configure` to set up your credentials.")
        sys.exit(1)


def _build_chain():
    from typing_extensions import TypedDict
    from langgraph.graph import StateGraph, START, END
    from clii.structured_output import Reply, structured_llm
    from clii.tools import type_print, type_command

    class State(TypedDict):
        messages: list
        reply: Reply

    def llm_node(state: State):
        output = structured_llm.invoke(state["messages"])
        return {"reply": output}

    def terminal_command_node(state: State):
        type_command(state["reply"].command)
        return {}

    def llm_answer_node(state: State):
        type_print(state["reply"].answer)
        return {}

    def router(state: State):
        return "terminal_command_node" if state["reply"].command is not None else "llm_answer_node"

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
    return workflow.compile()


def _shell_init_command():
    from clii.tools import shell_init

    shell_init(sys.argv[2] if len(sys.argv) > 2 else "zsh")


# Reserved keywords matched against sys.argv[1] before argparse ever runs.
# These need config-free, config-file-free dispatch, and none of them can be
# expressed as ordinary argparse positionals alongside a bare free-text query
# (see main.py history/discussion for why).
RESERVED_COMMANDS = {
    "configure": configure,
    "shell-init": _shell_init_command,
}


def main():
    parser = argparse.ArgumentParser(
        prog="clii",
        description="Natural language terminal assistant for macOS",
    )
    parser.add_argument("query", nargs="?", help="Natural language query (must be a single quoted string)")

    if len(sys.argv) > 1 and sys.argv[1] in RESERVED_COMMANDS:
        RESERVED_COMMANDS[sys.argv[1]]()
        return

    args = parser.parse_args()

    _check_config()
    chain = _build_chain()

    if args.query:
        chain.invoke({"messages": [{"role": "user", "content": args.query}]})
    else:
        from langchain_core.messages import HumanMessage, AIMessage
        from clii.tools import multiline_input

        # Interactive REPL
        print(r"""
 ██████╗██╗     ██╗██╗
██╔════╝██║     ██║██║
██║     ██║     ██║██║
██║     ██║     ██║██║
╚██████╗███████╗██║██║
 ╚═════╝╚══════╝╚═╝╚═╝
""")
        print("clii interactive mode — type your query or Ctrl-C to exit")
        print("(Enter submits, Alt+Enter inserts a newline, paste is safe)")
        history = []
        try:
            while True:
                user_query = multiline_input("> ").strip()
                if not user_query:
                    continue
                history.append(HumanMessage(content=user_query))
                result = chain.invoke({"messages": history})
                reply = result["reply"]
                if reply.command is not None:
                    # terminal_command_node already wrote the command to the
                    # shell's buffer file; exit now so the shell wrapper picks
                    # it up immediately, same as one-shot `clii "..."` usage.
                    return
                history.append(AIMessage(content=reply.answer))
        except KeyboardInterrupt:
            print()


if __name__ == "__main__":
    main()
