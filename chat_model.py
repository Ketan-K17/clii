from langchain_openai import AzureChatOpenAI
from decouple import config


llm = AzureChatOpenAI(
    azure_deployment=config("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
    api_key=config("AZURE_OPENAI_CHAT_KEY"),
    azure_endpoint=config("AZURE_OPENAI_CHAT_ENDPOINT"),
    model=config("AZURE_OPENAI_CHAT_MODEL"),
    api_version=config("AZURE_API_VERSION"),
    temperature=config("LLM_TEMPERATURE"),
)

if __name__ == "__main__":
    print(llm.invoke("hi").content)


