# AutoBook

Automated book generation system with a human-in-the-loop editorial workflow.

## What It Does

- Create a book from a title and initial notes
- Generate an outline and pause for editor review
- Regenerate the outline when revision notes are submitted
- Generate chapters sequentially using summaries of approved earlier chapters
- Approve chapters or request revisions until the planned chapter count is complete
- Send optional SMTP or Microsoft Teams notifications
- Export the final manuscript as `docx` or `pdf` only after final approval

## Stack

- Backend: FastAPI
- Database: Supabase
- AI: OpenRouter-compatible chat models
- Frontend: React + Vite
- Output: `python-docx`, `reportlab`

## Architecture

The system follows a simple modular flow that matches the project brief:

1. Input and Seeding
- A book is created from title + notes in the dashboard or imported from `.csv` / `.xlsx`
- The original brief is stored as `notes_on_outline_before`

2. Outline Generation and Review
- The backend generates an outline through the AI layer
- The outline is saved in Supabase and paused for editor review
- The editor can approve or request revision through the dashboard

3. Chapter Engine and Context Chaining
- After outline approval, chapters are generated sequentially
- Each approved chapter is summarized and stored
- Later chapter prompts use those summaries to preserve continuity

4. Completion and Final Export
- When the planned chapter count is fully approved, the manuscript is marked complete
- Final export becomes available as `docx` or `pdf`

5. Notifications
- The backend can notify the editor through SMTP email or Teams webhook when review is needed or the book is complete

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
2. Start the API with one of these commands:

From the project root:

```powershell
uvicorn backend.main:app --reload
```

From inside the `backend/` folder:

```powershell
uvicorn dev_server:app --reload
```

Simplest option from inside `backend/`:

```powershell
python run_backend.py
```

3. In `frontend/`, run `npm install`
4. Run `npm run dev`

## Current Workflow

1. Create a new book with title and notes.
2. Review the generated outline.
3. Approve the outline or request revision.
4. Generate chapters one by one.
5. Approve each chapter or request revision.
6. When the last planned chapter is approved, the system automatically marks the book as complete.
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

### Brief Field Alignment

The project brief uses some field names that differ from this app's original internal naming. The API now exposes brief-style aliases so the implementation maps more directly to the document:

- `notes_on_outline_before`: the initial `book.notes` value used before outline generation
- `status_outline_notes`: the current outline review state derived from the latest outline and book workflow status
- `chapter_notes_status`: the review state of each chapter
- `no_notes_needed`: `true` when the manuscript has reached final completion and export is allowed

## Submission Checklist

- Code repository: complete
- DB schema description: see [docs/schema.md](/c:/Users/osama/OneDrive/Desktop/Automated%20Book%20Generation%20System/docs/schema.md:1)
- Requirement mapping: included in this README
- Dashboard screenshots: still needed
- Video demonstration: still needed
- Sample generated `.docx` or `.pdf`: still needed
- Demo checklist and script: see [docs/submission_checklist.md](/c:/Users/osama/OneDrive/Desktop/Automated%20Book%20Generation%20System/docs/submission_checklist.md:1)

## Presentation Pack

Use these project files during final submission preparation:

- Demo checklist and video speaking script: [docs/submission_checklist.md](/c:/Users/osama/OneDrive/Desktop/Automated%20Book%20Generation%20System/docs/submission_checklist.md:1)
- Database schema reference: [docs/schema.md](/c:/Users/osama/OneDrive/Desktop/Automated%20Book%20Generation%20System/docs/schema.md:1)
- Spreadsheet import template: [docs/import_template.csv](/c:/Users/osama/OneDrive/Desktop/Automated%20Book%20Generation%20System/docs/import_template.csv:1)
- Optional Supabase brief-column migration: [docs/supabase_brief_column_migration.sql](/c:/Users/osama/OneDrive/Desktop/Automated%20Book%20Generation%20System/docs/supabase_brief_column_migration.sql:1)
