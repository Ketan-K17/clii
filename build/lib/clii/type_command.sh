#!/bin/bash
# Usage: ./type_command.sh "string to type"
# Re-launches itself in the background so typing starts after the prompt returns.

if [ $# -eq 0 ]; then
    echo "Usage: $0 <string to type>"
    exit 1
fi

# If not already in background mode, re-spawn and exit so the prompt returns first
if [[ "$1" != "--bg" ]]; then
    ("$0" --bg "$@") &
    exit 0
fi

shift  # strip --bg flag
input="$*"

# Remember which app invoked us, so the keystrokes go back to this terminal even
# if focus drifts before we start typing.
target=$(osascript -e 'tell application "System Events" to name of first process whose frontmost is true' 2>/dev/null)

# Give the shell time to finish drawing its prompt and hand the tty to its line
# editor. Typing into a mid-redraw terminal is how characters get dropped.
sleep 0.6

# Send the whole string in a single keystroke call. Splitting it into chunks
# meant one osascript process per chunk, and characters landing on a chunk
# boundary were routinely lost. Text is passed via argv so quotes, backslashes
# and dashes need no escaping.
osascript - "$input" "$target" <<'APPLESCRIPT'
on run argv
    set theText to item 1 of argv
    set theTarget to item 2 of argv
    tell application "System Events"
        if theTarget is not "" then
            try
                set frontmost of process theTarget to true
                delay 0.1
            end try
        end if
        keystroke theText
    end tell
end run
APPLESCRIPT

if [ $? -ne 0 ]; then
    echo >&2
    echo "clii: could not type the command." >&2
    echo "Grant Accessibility permission to your terminal in" >&2
    echo "System Settings > Privacy & Security > Accessibility." >&2
fi
