# AutoBook — Database Schema

## Table: books

| Column     | Type      | Constraints          | Description                  |
|------------|-----------|----------------------|------------------------------|
| id         | uuid      | PK, auto-generated   | Unique book identifier       |
| title      | text      | NOT NULL             | Book title                   |
| notes      | text      |                      | Author's initial brief       |
| status     | text      | NOT NULL             | Current pipeline stage       |
| created_at | timestamp | default now()        | Creation timestamp           |

**Status values:**
`generating` → `waiting_for_review` → `outline_approved`
→ `chapters_in_progress` → `chapters_complete`

---

## Table: outlines

| Column       | Type      | Constraints        | Description                        |
|--------------|-----------|--------------------|------------------------------------|
| id           | uuid      | PK, auto-generated | Unique outline identifier          |
| book_id      | uuid      | FK → books.id      | Parent book                        |
| content      | text      |                    | Full outline text                  |
| status       | text      | NOT NULL           | Review state                       |
| editor_notes | text      |                    | Editor feedback for regeneration   |
| created_at   | timestamp | default now()      | Creation timestamp                 |

**Status values:** `waiting_for_review` → `approved` | `needs_revision`

---

## Table: chapters

| Column         | Type      | Constraints        | Description                        |
|----------------|-----------|--------------------|------------------------------------|
| id             | uuid      | PK, auto-generated | Unique chapter identifier          |
| book_id        | uuid      | FK → books.id      | Parent book                        |
| chapter_number | integer   | NOT NULL           | Sequential position (1, 2, 3…)     |
| content        | text      |                    | Full chapter body text             |
| summary        | text      |                    | AI-generated summary for chaining  |
| status         | text      | NOT NULL           | Review state                       |
| editor_notes   | text      |                    | Editor feedback for regeneration   |
| created_at     | timestamp | default now()      | Creation timestamp                 |

**Status values:** `waiting_for_review` → `approved` | `needs_revision`

---

## Pipeline Flow

```
books:     generating
               ↓
           waiting_for_review   ← outline generated, editor must review
               ↓
           outline_approved     ← editor approved outline
               ↓
           chapters_in_progress ← chapter generation underway
               ↓
           chapters_complete    ← final chapter marked as done

outlines:  waiting_for_review → approved
                              → needs_revision → (regenerated) → waiting_for_review

chapters:  waiting_for_review → approved
                              → needs_revision → (regenerated) → waiting_for_review
```

---

## Notes

- Every table uses Supabase auto-generated UUIDs as primary keys.
- `chapters.summary` is populated by the AI after a chapter is approved
  and is injected into the prompt for the next chapter to maintain
  narrative continuity.
- `editor_notes` on both `outlines` and `chapters` stores the feedback
  text submitted by the editor when requesting a revision.
