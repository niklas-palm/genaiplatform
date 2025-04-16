from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union

class Message(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    n: Optional[int] = Field(default=1, ge=1)
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    
    @validator('messages')
    def validate_messages(cls, v):
        if not v:
            raise ValueError("messages cannot be empty")
        return v