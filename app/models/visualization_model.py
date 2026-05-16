from pydantic import BaseModel

class OverlayRequest(BaseModel):
	analysis_id: str
