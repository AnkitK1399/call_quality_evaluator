from pydantic import BaseModel
from typing import Optional

class PathInputRequest(BaseModel):
    file_path: str
    file_path_2: Optional[str] = None


class FollowUpRequest(BaseModel):
    evaluation_id: int
    question: str
