```
 ██████╗██╗     ██╗██╗
██╔════╝██║     ██║██║
██║     ██║     ██║██║
██║     ██║     ██║██║
╚██████╗███████╗██║██║
 ╚═════╝╚══════╝╚═╝╚═╝
```

**clii** is a natural language terminal assistant for macOS. Type what you want in plain English, and it either types the equivalent shell command into your terminal for you to review and run, or answers your question directly.

## Setup (macOS)

### 1. Prerequisites

- macOS
- Python 3.11+
- An LLM provider you can connect to: [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service) credentials, or a local [Ollama](https://ollama.com) install

### 2. Install

**Option A: Homebrew (recommended)**

```bash
brew tap Ketan-K17/clii
brew install clii
```

**Option B: From source**

Clone the repo and install it into a virtual environment:

```bash
git clone https://github.com/<your-username>/clii.git
cd clii
python3 -m venv clii_venv
source clii_venv/bin/activate
pip install -e .
```

### 3. Configure your model provider

Run the setup wizard and follow the prompts:

```bash
clii configure
```

This walks you through selecting a provider (Azure OpenAI or Ollama) and saves your credentials to `~/.config/clii/.env`.

### 4. Enable terminal typing (recommended)

By default, `clii` needs a way to place generated commands directly into your terminal's input line so you can review before running them. Add this to your `~/.zshrc`:

```bash
eval "$(clii shell-init)"
```

Then reload your shell:

```bash
exec zsh
```

Without this step, `clii` still works, but falls back to a less seamless way of surfacing commands.

## Usage

**Ask it to do something:**

```bash
$ clii "list all docker containers"
```

`clii` types `docker ps -a` into your terminal prompt — you hit Enter to run it (or edit it first).

**Ask it a question:**

```bash
$ clii "what's the difference between grep and egrep"
```

`clii` prints a plain-language answer instead of a command.

You can also drop into interactive mode by running `clii` with no arguments, then keep typing queries at the `>` prompt until you exit with `Ctrl-C`.

## Chat history

`clii` remembers recent turns so follow-up queries (like "no, exclude X") can refer back to what it last suggested. This session is stored at `~/.config/clii/session.json`.

**View or edit it:**

```bash
clii history
```

This opens the saved history in `$EDITOR` (`nano` by default) as plain text, with `>` marking your queries and `<` marking clii's replies. Edit or delete turns, then save and quit to update what clii remembers.

**Erase it:**

- Delete all lines in the `clii history` editor and save — clii clears the session.
- Or start a query with `--new` to ignore and wipe any existing session first:

  ```bash
  clii --new "your query"
  ```

- Or delete the file directly:

  ```bash
  rm ~/.config/clii/session.json
  ```
