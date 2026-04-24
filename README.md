# AutoBook

Automated book generation system with a human-in-the-loop editorial workflow.

## What It Does

- Create a book from a title and initial notes
- Generate an outline and pause for editor review
- Regenerate the outline when revision notes are submitted
- Generate chapters sequentially using summaries of approved earlier chapters
- Approve, revise, or mark the last chapter as the final chapter
- Send optional SMTP or Microsoft Teams notifications
- Export the final manuscript as `docx`, `pdf`, or `txt` only after final approval

## Stack

- Backend: FastAPI
- Database: Supabase
- AI: OpenRouter-compatible chat models
- Frontend: React + Vite
- Output: `python-docx`, `reportlab`

## Main API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/books/create-stream` | Create a book and stream outline generation |
| `POST` | `/books/import` | Import books from `.csv` or `.xlsx` for batch seeding |
| `GET` | `/books` | List all books |
| `GET` | `/books/{id}` | Get a book and its latest outline |
| `POST` | `/books/{id}/feedback` | Approve or revise the outline |
| `GET` | `/books/{id}/chapters` | List book chapters |
| `POST` | `/books/{id}/generate-chapter-stream` | Stream the next chapter |
| `POST` | `/chapters/{id}/feedback` | Approve, revise, or mark final chapter |
| `GET` | `/books/{id}/compile?format=docx` | Export after final approval |

## Environment Variables

Backend:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENROUTER_API_KEY=your_openrouter_api_key
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_TO=
TEAMS_WEBHOOK=
```

Frontend:

```env
VITE_API_URL=http://127.0.0.1:8000
```

## Local Run

1. Install backend dependencies from `requirements.txt`
2. Start the API with `uvicorn main:app --reload`
3. In `frontend/`, run `npm install`
4. Run `npm run dev`

## Current Workflow

1. Create a new book with title and notes.
2. Review the generated outline.
3. Approve the outline or request revision.
4. Generate chapters one by one.
5. Approve each chapter or request revision.
6. Mark the last approved chapter as `Final Chapter`.
7. Export the completed manuscript.

## Spreadsheet Import

The project now supports local spreadsheet seeding for the "Google Sheets or Local Excel" requirement.

- Supported formats: `.csv`, `.xlsx`
- Required columns: `title`, `notes`
- Endpoint: `POST /books/import`
- Query option: `generate_outlines=true|false`

Example flow:

- Export a Google Sheet as `.csv`, or prepare a local Excel file.
- Upload it to `/books/import`.
- When `generate_outlines=true`, each imported book enters the normal review pipeline with an outline ready for review.

## Requirement Mapping

- Gated outline pipeline: implemented through `/books/create`, `/books/create-stream`, and `/books/{id}/feedback`
- Context-aware chapter engine: implemented through summary storage plus sequential chapter generation
- Monitoring dashboard: implemented in the React frontend
- Notifications: implemented with SMTP and Teams webhook support
- Final compilation: implemented and now blocked until final approval
- Local Excel / spreadsheet input: implemented through `/books/import`
- Source-backed research: not implemented because it is optional in the brief

## Submission Checklist

- Code repository: complete
- DB schema description: see [docs/schema.md](/c:/Users/osama/OneDrive/Desktop/Automated%20Book%20Generation%20System/docs/schema.md:1)
- Requirement mapping: included in this README
- Dashboard screenshots: still needed
- Video demonstration: still needed
- Sample generated `.docx` or `.pdf`: still needed
