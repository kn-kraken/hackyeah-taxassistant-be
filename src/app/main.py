from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.schemas.requests import ChatCompletionRequest
from app.schemas.responses import (
    ChatCompletionOkResponseData,
    ChatCompletionOkResponse, 
    ChatCompletionErrorResponse
)

app = FastAPI()


@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


@app.post("/chat/completions")
async def chat_completions(
    request_payload: ChatCompletionRequest    
    ) -> ChatCompletionOkResponse | ChatCompletionErrorResponse:
    return ChatCompletionOkResponse(
        data=ChatCompletionOkResponseData(
            content="Hello, World!"
        )
    )
