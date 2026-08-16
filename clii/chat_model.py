from decouple import Config, RepositoryEnv
import os

_config_path = os.path.expanduser("~/.config/clii/.env")
_config = Config(RepositoryEnv(_config_path))

PROVIDER = _config("LLM_PROVIDER", default="azure").lower()

def _ollama_headers():
    """Auth headers for Ollama.

    Only needed when OLLAMA_BASE_URL points straight at https://ollama.com.
    A local server proxying `*:cloud` models signs its own requests with
    ~/.ollama/id_ed25519, so no key is required there.
    """
    api_key = _config("OLLAMA_API_KEY", default="").strip()
    return {"Authorization": f"Bearer {api_key}"} if api_key else {}


def _ollama_reasoning(base_url: str, model: str, headers: dict):
    """Value for ChatOllama(reasoning=...), i.e. Ollama's `think` field.

    Reasoning models default to thinking, which either wastes tokens before
    every command or (with structured output) lands the whole response in the
    `thinking` field and leaves content empty. So we want `think: false` —
    but Ollama rejects `think` entirely for models without the capability,
    hence the /api/show probe. OLLAMA_REASONING overrides: off/false to force
    it off, or true/low/medium/high to keep reasoning on.
    """
    override = _config("OLLAMA_REASONING", default="auto").strip().lower()
    if override in ("off", "false", "no", "0"):
        return False
    if override in ("on", "true", "yes", "1"):
        return True
    if override in ("low", "medium", "high"):
        return override

    import json
    import urllib.error
    import urllib.request

    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/show",
        data=json.dumps({"model": model}).encode(),
        headers={"Content-Type": "application/json", **headers},
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            capabilities = json.load(response).get("capabilities") or []
    except (urllib.error.URLError, OSError, ValueError):
        # Server down or an older Ollama without /api/show: leave `think`
        # unset rather than risk a 400 on every call.
        return None
    return False if "thinking" in capabilities else None


if PROVIDER == "ollama":
    from langchain_ollama import ChatOllama

    _model = _config("OLLAMA_MODEL", default="llama3.2")
    _base_url = _config("OLLAMA_BASE_URL", default="http://localhost:11434")

    _headers = _ollama_headers()

    llm = ChatOllama(
        model=_model,
        base_url=_base_url,
        temperature=float(_config("LLM_TEMPERATURE", default=0.0)),
        reasoning=_ollama_reasoning(_base_url, _model, _headers),
        client_kwargs={"headers": _headers} if _headers else None,
    )
elif PROVIDER == "openai":
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        api_key=_config("OPENAI_API_KEY"),
        model=_config("OPENAI_MODEL", default="gpt-4o"),
        temperature=float(_config("LLM_TEMPERATURE", default=0.0)),
    )
else:
    from langchain_openai import AzureChatOpenAI

    llm = AzureChatOpenAI(
        azure_deployment=_config("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
        api_key=_config("AZURE_OPENAI_CHAT_KEY"),
        azure_endpoint=_config("AZURE_OPENAI_CHAT_ENDPOINT"),
        model=_config("AZURE_OPENAI_CHAT_MODEL"),
        api_version=_config("AZURE_API_VERSION"),
        temperature=_config("LLM_TEMPERATURE"),
    )

if __name__ == "__main__":
    print(llm.invoke("hi").content)
