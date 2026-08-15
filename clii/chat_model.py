from decouple import Config, RepositoryEnv
import os

_config_path = os.path.expanduser("~/.config/clii/.env")
_config = Config(RepositoryEnv(_config_path))

PROVIDER = _config("LLM_PROVIDER", default="azure").lower()

if PROVIDER == "ollama":
    from langchain_ollama import ChatOllama

    llm = ChatOllama(
        model=_config("OLLAMA_MODEL", default="llama3.2"),
        base_url=_config("OLLAMA_BASE_URL", default="http://localhost:11434"),
        temperature=float(_config("LLM_TEMPERATURE", default=0.0)),
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
