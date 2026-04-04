#!/bin/bash
# Usage: ./test.sh "string to type"
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
length=${#input}

# Wait for the shell to return to the prompt
sleep 0.3

for (( i=0; i<length; i+=3 )); do
    chunk="${input:$i:3}"
    chunk="${chunk//\\/\\\\}"
    chunk="${chunk//\"/\\\"}"
    osascript -e "tell application \"System Events\" to keystroke \"$chunk\""
done
