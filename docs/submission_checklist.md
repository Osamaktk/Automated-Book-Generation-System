# Submission Checklist

## Code Repository
- [x] Clean GitHub repository with documented README
- [x] All source code committed — backend (FastAPI), frontend (React + Vite)
- [x] Environment variable reference in `.env.example`

## Database Schema
- [x] Schema documented in `docs/schema.md` with full table definitions and status flow
- [x] Migration SQL for brief-aligned columns in `docs/supabase_brief_column_migration.sql`

## Dashboard Access
- [x] Screenshots of all major workflow stages in `docs/images/screenshots/`
  - Dashboard library view
  - Outline waiting for review
  - Brief-aligned fields panel
  - Outline actions and story context
  - Book completion state
  - Final export screen
  - Email notifications

## Sample Output
- [x] Generated manuscript in `docs/sample-output.docx`

## Video Demonstration
- [ ] Recording covering architecture walkthrough and Title-to-Draft pipeline demo
- [ ] Includes dashboard interaction (outline approval, chapter review, export)

## Brief Field Alignment
- [x] `notes_on_outline_before` — used in DB, API, and UI
- [x] `status_outline_notes` — used in DB, API, and UI
- [x] `chapter_notes_status` — used in DB, API, and UI
- [x] `no_notes_needed` — used in DB, API, and UI
