# AutoBook Frontend

React + Vite dashboard for the AutoBook editorial workflow.

## Environment

Create `frontend/.env`:

```env
VITE_API_URL=http://127.0.0.1:8000
```

## Local Development

1. Run `npm install`
2. Run `npm run dev`
3. Open the Vite URL in your browser

The frontend expects the API to be running from the project root with:

```powershell
uvicorn backend.main:app --reload
```

## Routes

- `/dashboard`
- `/books/:bookId`
- `/books/:bookId/chapters/:chapterId`

## Workflow in the UI

- Create a manuscript from title and notes
- Review or revise the generated outline
- Generate chapters sequentially
- Review each chapter and request revisions when needed
- Approve the planned chapters until the book is automatically marked complete
- Download the completed manuscript after final approval
