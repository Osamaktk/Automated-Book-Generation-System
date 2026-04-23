from pydantic import BaseModel


class BookInput(BaseModel):
    title: str
    notes: str


class EditorFeedback(BaseModel):
    status: str
    editor_notes: str = ""


class ShareUserInput(BaseModel):
    shared_with: str
