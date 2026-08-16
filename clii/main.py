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

OPENAI_CONFIG_KEYS = [
    ("OPENAI_API_KEY", "OpenAI API Key"),
    ("OPENAI_MODEL", "Model Name (e.g. gpt-4o)"),
    ("LLM_TEMPERATURE", "Temperature (e.g. 0)"),
]


PROVIDERS = [
    ("azure", "AzureChatOpenai", AZURE_CONFIG_KEYS),
    ("ollama", "Ollama", OLLAMA_CONFIG_KEYS),
    ("openai", "OpenAI", OPENAI_CONFIG_KEYS),
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

    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            existing_lines = f.read().splitlines()
    else:
        existing_lines = []

    existing_config = dict(
        line.split("=", 1) for line in existing_lines if "=" in line
    )
    has_existing_config = all(existing_config.get(key) for key, _ in config_keys)

    new_values = {"LLM_PROVIDER": provider}
    if has_existing_config:
        use_existing = select_menu("Use existing config?", ["Yes", "No"]) == 0
    else:
        use_existing = False

    if use_existing:
        print(f"Switching provider to {provider}, keeping existing config.")
    else:
        for key, label in config_keys:
            new_values[key] = input(f"{label}: ").strip()

    lines = []
    for line in existing_lines:
        key = line.split("=", 1)[0] if "=" in line else None
        if key in new_values:
            lines.append(f"{key}={new_values.pop(key)}")
        else:
            lines.append(line)

    # LLM_PROVIDER should always be present near the top for new configs.
    if "LLM_PROVIDER" in new_values:
        lines.insert(0, f"LLM_PROVIDER={new_values.pop('LLM_PROVIDER')}")

    for key, value in new_values.items():
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


def _history_command():
    from clii.tools import edit_history

    edit_history()


# Reserved keywords matched against sys.argv[1] before argparse ever runs.
# These need config-free, config-file-free dispatch, and none of them can be
# expressed as ordinary argparse positionals alongside a bare free-text query
# (see main.py history/discussion for why).
RESERVED_COMMANDS = {
    "configure": configure,
    "shell-init": _shell_init_command,
    "history": _history_command,
}


def main():
    parser = argparse.ArgumentParser(
        prog="clii",
        description="Natural language terminal assistant for macOS",
    )
    parser.add_argument("query", nargs="?", help="Natural language query (must be a single quoted string)")
    parser.add_argument(
        "--new", action="store_true",
        help="Ignore any resumable session from a previous invocation and start fresh",
    )

    if len(sys.argv) > 1 and sys.argv[1] in RESERVED_COMMANDS:
        RESERVED_COMMANDS[sys.argv[1]]()
        return

    args = parser.parse_args()

    _check_config()
    chain = _build_chain()

    from langchain_core.messages import HumanMessage, AIMessage
    from clii.session import load_session, save_session, clear_session

    if args.new:
        clear_session()

    if args.query:
        history = load_session()
        history.append(HumanMessage(content=args.query))
        result = chain.invoke({"messages": history})
        reply = result["reply"]
        if reply.command is not None:
            # Remember what we suggested, not just that we replied, so a
            # follow-up invocation ("no, exclude X") can refer back to it.
            history.append(AIMessage(content=f"(suggested command: {reply.command})"))
        else:
            history.append(AIMessage(content=reply.answer))
        save_session(history)
    else:
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
        history = load_session()
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
                    history.append(AIMessage(content=f"(suggested command: {reply.command})"))
                    save_session(history)
                    return
                history.append(AIMessage(content=reply.answer))
        except KeyboardInterrupt:
            print()
            save_session(history)


if __name__ == "__main__":
    main()
