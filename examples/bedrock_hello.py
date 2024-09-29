import ell
from PIL import Image
from ell.providers.bedrock import BedrockProvider
from pydantic import BaseModel, Field
import anthropic
from typing import List
import ell
from ell.types import Message
import boto3

@ell.simple(model="anthropic.claude-3-haiku-20240307-v1:0", api_params={"stream":True}, client=boto3.client('bedrock-runtime', region_name='us-east-1'))
def hello_from_bedrock_streaming():
    """You are an AI assistant. Your task is to respond to the user's message with a friendly greeting."""
    return "Say hello to the world!!!"

@ell.simple(model="anthropic.claude-3-haiku-20240307-v1:0", client=boto3.client('bedrock-runtime', region_name='us-east-1'))
def hello_from_bedrock():
    """You are an AI assistant. Your task is to respond to the user's message with a friendly greeting."""
    return "Say hello to the world!!!"

@ell.simple(model="anthropic.claude-3-haiku-20240307-v1:0", client=boto3.client('bedrock-runtime', region_name='us-east-1'))
def describe_activity(image: Image.Image):
    return [
        ell.system("You are VisionGPT. Answer <5 words all lower case."),
        ell.user(["Describe what the person in the image is doing:", image])
    ]


@ell.tool()
def approve_claim(claim_id : str):
    """Approve a claim"""
    return f"approved {claim_id}"

@ell.complex(model="anthropic.claude-3-haiku-20240307-v1:0", tools=[approve_claim], client=boto3.client('bedrock-runtime', region_name='us-east-1'))
def insurance_claim_chatbot(message_history: str) -> str:
    """You are an insurance claim approver. You can use a tool to approve a claim if an id is given to you."""
    return message_history


if __name__ == "__main__":
    ell.init(verbose=True, store="./logdir", autocommit=True)
    hello_from_bedrock_streaming()
    hello_from_bedrock()
    # Capture an image from the webcam
    describe_activity(Image.open(r"./examples/future/catmeme.jpg")) # "they are holding a book"

    message_history = []

    # Run through messages automatically!
    user_messages = "Please approve the claim 12344534"

    response_message = insurance_claim_chatbot(user_messages)
    print(response_message)
    if response_message.tool_calls:
        tool_results = response_message.call_tools_and_collect_as_message()
        print(tool_results)
    print('THE END')