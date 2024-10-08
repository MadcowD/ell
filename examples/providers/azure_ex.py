import ell2a
import openai
import os
ell2a.init(verbose=True, store='./logdir')

# your subscription key
subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
# Your Azure OpenAI resource https://<your resource name>.openai.azure.com/
azure_endpoint = "https://<your resource name>.openai.azure.com/"
# Option 2: Use a client directly
azureClient = openai.AzureOpenAI(
    azure_endpoint = azure_endpoint,
    api_key = subscription_key,
    api_version = "2024-05-01-preview",
)
# (Recommended) Option 1: Register all the models on your Azure resource & use your models automatically
ell2a.config.register_model("<your-azure-model-deployment-name>", azureClient)

@ell2a.simple(model="<your-azure-model-deployment-name>")
def write_a_story(about : str):
    return f"write me a story about {about}!"

write_a_story("cats")


# Option 2: Use a client directly
azureClient = openai.AzureOpenAI(
    azure_endpoint = azure_endpoint,
    api_key = subscription_key,
    api_version = "2024-05-01-preview",
)

@ell2a.simple(model="<your-azure-model-deployment-name>", client=azureClient)
def write_a_story(about : str):
    return f"write me a story about {about}"

write_a_story("cats")
