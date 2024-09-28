from typing import Literal
from pydantic import BaseModel


class ChatCompletionOkResponseData(BaseModel):
    type: Literal["text"] = "text"
    content: str


class ChatCompletionOkResponse(BaseModel):
    type: str = "ok"
    data: ChatCompletionOkResponseData


class ChatCompletionErrorResponse(BaseModel):
    type: str = "error"
    message: str

