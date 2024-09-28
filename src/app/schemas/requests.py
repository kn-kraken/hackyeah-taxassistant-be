from pydantic import BaseModel


class ChatCompletionRequest(BaseModel):
    user_message: str
    user_id: str
    conversation_id: str
