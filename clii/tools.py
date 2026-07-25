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
        if [[ -n $_CLII_HOOK_INSTALLED ]]; then
            # The line-init hook will type this into the buffer. Going through
            # the hook rather than `print -z` avoids one frame in which zsh
            # renders the whole command before the animation can clear it.
            _CLII_PENDING="$(<$_clii_cmd_file)"
        else
            print -z -- "$(<$_clii_cmd_file)"
        fi
    fi
    rm -f "$_clii_cmd_file"
    return $_clii_status
}

# Typing animation: reveal the pending command a few characters at a time as
# the line editor starts, then leave it in the buffer, editable and unexecuted.
# Purely cosmetic. If the hook cannot be installed the function above falls
# back to `print -z` and the command simply appears all at once.
: ${CLII_TYPE_CHUNK:=3}     # characters revealed per step
: ${CLII_TYPE_DELAY:=3}     # pause per step, in hundredths of a second

zmodload zsh/zselect 2>/dev/null

_clii_line_init() {
    [[ -n $_CLII_PENDING ]] || return 0
    local text=$_CLII_PENDING i
    _CLII_PENDING=
    for (( i = 1; i <= $#text; i += CLII_TYPE_CHUNK )); do
        BUFFER=${text[1,i + CLII_TYPE_CHUNK - 1]}
        CURSOR=$#BUFFER
        zle -R
        # zselect with no fds is just a sleep, and unlike `sleep` it does not
        # fork a process on every single step.
        zselect -t $CLII_TYPE_DELAY 2>/dev/null
    done
    BUFFER=$text
    CURSOR=$#BUFFER
    zle -R
}

# add-zle-hook-widget chains onto any existing line-init hook rather than
# replacing it. Overriding zle-line-init directly recursed on the second eval,
# because powerlevel10k re-wraps whatever widget it finds there.
if [[ -z $_CLII_HOOK_INSTALLED ]]; then
    autoload -Uz add-zle-hook-widget
    zle -N _clii_line_init
    if add-zle-hook-widget line-init _clii_line_init 2>/dev/null; then
        _CLII_HOOK_INSTALLED=1
    fi
fi
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
    which pushes straight onto the line editor buffer. A zle-line-init widget
    installed by the same snippet replays that buffer a few characters at a
    time, so the command still looks like it is being typed.

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
