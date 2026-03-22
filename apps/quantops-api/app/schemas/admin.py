from pydantic import BaseModel

class AdminListResponse(BaseModel):
    items: list[dict]
