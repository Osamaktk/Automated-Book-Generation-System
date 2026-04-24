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

## Routes

- `/dashboard`
- `/books/:bookId`
- `/books/:bookId/chapters/:chapterId`

## Workflow in the UI

- Create a manuscript from title and notes
- Review or revise the generated outline
- Generate chapters sequentially
- Review each chapter and request revisions when needed
- Mark the last chapter as `Final Chapter`
- Download the completed manuscript after final approval
