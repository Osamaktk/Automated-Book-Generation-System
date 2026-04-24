from pydantic import BaseModel


class BookInput(BaseModel):
    title: str
    notes: str


class EditorFeedback(BaseModel):
    status: str
    editor_notes: str = ""
