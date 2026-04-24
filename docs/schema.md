# AutoBook Database Schema

## Table: books

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `uuid` | PK, auto-generated | Unique book identifier |
| `title` | `text` | NOT NULL | Book title |
| `notes` | `text` | nullable | Initial author/editor brief |
| `status` | `text` | NOT NULL | Current pipeline stage |
| `created_at` | `timestamp` | default now() | Creation timestamp |

Status flow:

`generating` -> `waiting_for_review` -> `outline_approved` -> `chapters_in_progress` -> `chapters_complete`

## Table: outlines

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `uuid` | PK, auto-generated | Unique outline identifier |
| `book_id` | `uuid` | FK -> books.id | Parent book |
| `content` | `text` | nullable | Full outline text |
| `status` | `text` | NOT NULL | Outline review status |
| `editor_notes` | `text` | nullable | Revision request notes |
| `created_at` | `timestamp` | default now() | Creation timestamp |

Outline status flow:

`waiting_for_review` -> `approved`

`waiting_for_review` -> `needs_revision` -> regenerated outline -> `waiting_for_review`

## Table: chapters

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `uuid` | PK, auto-generated | Unique chapter identifier |
| `book_id` | `uuid` | FK -> books.id | Parent book |
| `chapter_number` | `integer` | NOT NULL | Sequential chapter index |
| `content` | `text` | nullable | Full chapter text |
| `summary` | `text` | nullable | Short continuity summary for future prompts |
| `status` | `text` | NOT NULL | Chapter review status |
| `editor_notes` | `text` | nullable | Revision request notes |
| `created_at` | `timestamp` | default now() | Creation timestamp |

Chapter status flow:

`waiting_for_review` -> `approved`

`waiting_for_review` -> `needs_revision` -> regenerated chapter -> `waiting_for_review`

Final completion rule:

- The editor marks the final reviewed chapter with `final_chapter`
- The API converts that chapter to `approved`
- The parent book status becomes `chapters_complete`
- Compilation/export is allowed only after `chapters_complete`

## Narrative Continuity

- When a chapter is approved, the system generates and stores a short summary.
- Later chapter prompts inject approved chapter summaries to reduce narrative drift.
- This summary log functions as the project story bible.
