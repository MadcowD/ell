from typing import List
from pydantic import BaseModel, Field
import ell

ell.config.verbose = True


@ell.tool()
def create_claim_draft(claim_details: str, claim_type: str, claim_amount: float, 
                       claim_date : str = Field(description="The date of the claim in the format YYYY-MM-DD.")):
    """Create a claim draft. Returns the claim id created."""
    return "claim_id-123234"

@ell.tool()
def approve_claim(claim_id : str):
    """Approve a claim"""
    pass

@ell.multimodal(model="gpt-4o", tools=[create_claim_draft, approve_claim], temperature=0.1)
def insurance_claim_chatbot(message_history: List[str]):
    return [
        ell.system( """You are a an insurance adjuster AI. You are given a dialogue with a user and have access to various tools to effectuate the insurance claim adjustment process. Ask question until you have enough information to create a claim draft. Then ask for approval."""),
    ] + [
        ell.Message(role="user" if i % 2 == 0 else "assistant", content=message)
        for i, message in enumerate(message_history)
    ] 


if __name__ == "__main__":
    from ell.stores.sql import SQLiteStore
    ell.set_store(SQLiteStore('sqlite_example'), autocommit=True)

    done = False
    message_history = []
    while True:
        user_message = input("User: ")
        if user_message == "exit":
            break
        message_history.append(user_message)
        response = insurance_claim_chatbot(message_history)
        print(response)
        message_history.append(response)
        



# import openai




# class StrContent(BaseModel):
#     content: str
#     type : Literal["text"]


# class Message(BaseModel):
#     content: Union[StrContent, FunctionCall, Image, Audio]


# x = my_lm()
# if x.content.type == "text":
#     print(x.content.text)

# if x.text:
#     print(x.text)









# class Message(BaseModel):
#     text: str
#     image: str
#     tool_result: str
#     audio: str
#     function_call  : FunctionCall

# # class FunctionCall(BaseModel):
# #     name: str
# #     arguments: BaseModel
# #     fn : Callable
# #     def call(self):
# #         return self.fn(self.arguments)



# @ell.lm(model="claude-3.5-sonnet")
# def i_use_different_content_blocks():
#     return "asdasd"



# i_use_different_content_blocks()
# -> 
# [
#     {
#         "type": "text",
#         "content": "asdasd"
#     },
#     {
#         "type": "function_call",
#         "content": {
#             "name": "asdasd",
#             "arguments": "asdasd"
#         }
#     },
#     {
#         "type": "file",
#         "content": "asdasd"
#     }
# ]


# @ell.multimodal_lm(model="gpt-4o")
# def i_use_different_content_blocks():
#     return "asdasd"


# class MultimodalMessage(BaseModel):
#     text: str
#     image: str
#     tool_result: str
#     audio: str
#     function_call  : FunctionCall
#     _raw




# @ell.text_lm(model="gpt-4o")
# def i_use_different_content_blocks():
#     return "asdasd"



# # -> str





# TOOLS = [
#     tool1,
#     tool2,
#     tool3,
# ]
# @ell.lm(model="llama-3-8b-instruct")
# def i_use_tools(request : str):
#     return [
#         ell.system("You are a helpful assistant. You have access to the following tools:" + "\n" + tool.prompt()),
#         ell.user(request),
#     ]



# TOOLS = [
#     tool1,
#     tool2,
#     tool3,
# ]
# @ell.lm(model="gpt-4o", tools=TOOLS)
# def i_use_tools(request : str):
#     pass



# # It's our job to abstract different kidns of Foundation Models

# @ell.openai.lm(model="gpt-4o", tools=TOOLS)
# def i_use_tools(request : str):
#     pass


# # Throws an error: # llama lms do not support explicit tool calling ,you need to prompt this
# @ell.llama.lm(model="llama-3-8b-instruct", tools=TOOLS) 
# def i_use_tools(request : str):
#     pass

# # therefore : ->
# @ell.llama.lm(model="llama-3-8b-instruct")
# def i_use_tools(request : str):
#     return [
#         ell.system("You are a helpful assistant. You have access to the following tools:" + "\n" + tool.prompt()),
#         ell.user(request),
#     ]


# @ell.anthropic.lm(model="claude-3.5-sonnet")
# def i_use_tools(request : str):
#     return [
#         ell.system("You are a helpful assistant. You have access to the following tools:" + "\n" + tool.prompt()),
#         ell.user(request),
#     ]
# class AnthropicMessage(BaseModel):
#     content_blocks : List[ContentBlock]

# class ContentBlock(BaseModel):
#     type : Literal["text", "function_call", "file"]
#     content : str



# #------------------------------- -- Against øur design philosophy

# @ell.lm(model="gpt-4o")
# def i_use_tools(request : str):
#     return MessageCreationParams(
#         tools=tools,
#         message=[
#             ell.system("You are a helpful assistant. You have access to the following tools:" + "\n" + tool.prompt()),
#             ell.user(request),
#         ]
#     )


# @ell.lm(model="gpt-4o")
# def i_use_tools(request : str):
#     """Suystem prompt"""
#     return "user pomrpt"




# # --------------


# @ell.lm # ALLL STRING BASED GET FUCKEd
# def gn():
#     return "asdasd"

# gn() # ->  str



# @ell.omni(tools=TOOLS, structured_outputs=True) # Gives your raw return tpes form the mdoel
# def fn():
#     return "asdasd"

# fn() # -> OpenAI.ChatCompletion

# fn().choices[0].message.content 




# class ContnetBlock(BaseModel):
#     text :lstr
#     audio : lnumpy
#     image : lmnumpy
#     function_call : lFunctionCall


# T = TypeVar("ContentBlockType")
# class ContentBlock(BaseModel):
#     type: Literal["text", "audio", "image", "function_call"]
#     content : T


# class TextContent(BaseModel):
#     type: Literal["text"]
#     content: str