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

CONFIG_KEYS = [
    ("AZURE_OPENAI_CHAT_ENDPOINT", "Azure OpenAI Endpoint"),
    ("AZURE_OPENAI_CHAT_KEY", "Azure OpenAI Key"),
    ("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "Deployment Name"),
    ("AZURE_OPENAI_CHAT_MODEL", "Model Name"),
    ("AZURE_API_VERSION", "API Version"),
    ("LLM_TEMPERATURE", "Temperature (e.g. 0)"),
]


def configure():
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    print("Configuring clii — credentials will be saved to", CONFIG_PATH)
    lines = []
    for key, label in CONFIG_KEYS:
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
        user_query: str
        reply: Reply

    def llm_node(state: State):
        output = structured_llm.invoke(state["user_query"])
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


def main():
    parser = argparse.ArgumentParser(
        prog="clii",
        description="Natural language terminal assistant for macOS",
    )
    parser.add_argument("query", nargs="*", help="Natural language query")
    parser.add_argument("configure", nargs="?", help=argparse.SUPPRESS)

    # Handle `clii configure` as a positional
    if len(sys.argv) > 1 and sys.argv[1] == "configure":
        configure()
        return

    # `clii shell-init [zsh]` prints the shell function that lets clii drop
    # commands straight into the line editor buffer. Needs no config.
    if len(sys.argv) > 1 and sys.argv[1] == "shell-init":
        from clii.tools import shell_init

        shell_init(sys.argv[2] if len(sys.argv) > 2 else "zsh")
        return

    args = parser.parse_args()

    _check_config()
    chain = _build_chain()

    if args.query:
        user_query = " ".join(args.query)
        chain.invoke({"user_query": user_query})
    else:
        # Interactive REPL
        print("clii interactive mode — type your query or Ctrl-C to exit")
        try:
            while True:
                user_query = input("> ").strip()
                if not user_query:
                    continue
                chain.invoke({"user_query": user_query})
        except KeyboardInterrupt:
            print()


if __name__ == "__main__":
    main()
