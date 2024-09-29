from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.config import Config
from app.schemas.requests import ChatCompletionRequest
from app.schemas.responses import (
    ChatCompletionOkResponseData,
    ChatCompletionOkResponse, 
    ChatCompletionErrorResponse
)
from app.services.ai import LLMOrchestrator

app = FastAPI()
config = Config()
orchestrator = LLMOrchestrator.OpenAI(
    api_key=config.OPENAI_API_KEY,
    model_name=config.OPENAI_MODEL_NAME,
    azure_search_endpoint=config.AZURE_SEARCH_ENDPOINT,
    azure_search_key=config.AZURE_SEARCH_KEY,
    azure_search_index_name=config.AZURE_SEARCH_INDEX_NAME
)


@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


@app.post("/chat/completions")
async def chat_completions(
    request_payload: ChatCompletionRequest    
    ) -> ChatCompletionOkResponse | ChatCompletionErrorResponse:

    response = await orchestrator.process_message(
        message=request_payload.user_message,
        conversation_id=request_payload.conversation_id
    )

    return ChatCompletionOkResponse(
        data=ChatCompletionOkResponseData(
            content=response
        )
    )
