import time
import subprocess
import os
import sys

SHELL_INIT_ZSH = r'''clii() {
    local _clii_cmd_file
    _clii_cmd_file=$(mktemp -t clii) || return 1
    CLII_CMD_FILE="$_clii_cmd_file" command clii "$@"
    local _clii_status=$?
    if [[ -s $_clii_cmd_file ]]; then
        print -z -- "$(<$_clii_cmd_file)"
    fi
    rm -f "$_clii_cmd_file"
    return $_clii_status
}
'''


def type_print(answer: str, delay: float = 0.03):
    step = 3
    for i in range(0, len(answer), step):
        print(answer[i:i + step], end="", flush=True)
        time.sleep(delay)
    print()


def type_command(text: str):
    """Put `text` into the shell's input buffer, editable and not executed.

    Preferred path: the `clii` shell function (see `clii shell-init`) hands us a
    file via CLII_CMD_FILE and feeds what we write there to zsh's `print -z`,
    which pushes straight onto the line editor buffer.

    Fallback path: synthesise keystrokes via System Events. This is unreliable
    on shells with ZLE plugins such as zsh-syntax-highlighting or
    zsh-autosuggestions, which re-render the whole line on every keypress and
    drop characters when input arrives faster than they can keep up.
    """
    cmd_file = os.environ.get("CLII_CMD_FILE")
    if cmd_file:
        with open(cmd_file, "w") as f:
            f.write(text)
        return

    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "type_command.sh")
    subprocess.run(["bash", script, text], check=True)
    print(
        'clii: tip: characters can get dropped while typing. Add '
        '\'eval "$(clii shell-init)"\' to your ~/.zshrc (then `exec zsh`) '
        'for reliable, native command insertion.',
        file=sys.stderr,
    )


def shell_init(shell: str = "zsh"):
    """Print the shell function that enables buffer integration."""
    if shell != "zsh":
        print(
            f"clii: shell-init supports zsh only (got {shell!r}). "
            "Other shells fall back to synthesised keystrokes.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    print(SHELL_INIT_ZSH, end="")


if __name__ == "__main__":
    type_command("ls -a | grep 'sanity'")
