from pydantic import BaseModel


class PatchWorkflowRequest(BaseModel):
    title: str | None = None
    prompt: str | None = None
