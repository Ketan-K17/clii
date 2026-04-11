from langchain_openai import AzureChatOpenAI
from decouple import Config, RepositoryEnv
import os

_config_path = os.path.expanduser("~/.config/clii/.env")
_config = Config(RepositoryEnv(_config_path))

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
