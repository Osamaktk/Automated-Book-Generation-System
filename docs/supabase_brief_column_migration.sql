-- Optional schema alignment for the exact field names used in Project.docx.
-- Run this in the Supabase SQL editor only if you want literal column names in storage,
-- not just API aliases.

alter table public.books
  add column if not exists notes_on_outline_before text,
  add column if not exists status_outline_notes text,
  add column if not exists no_notes_needed boolean default false;

update public.books
set
  notes_on_outline_before = coalesce(notes_on_outline_before, notes),
  status_outline_notes = coalesce(
    status_outline_notes,
    case
      when status in ('outline_approved', 'chapters_in_progress', 'chapters_complete') then 'approved'
      when status = 'waiting_for_review' then 'waiting_for_review'
      else status
    end
  ),
  no_notes_needed = coalesce(no_notes_needed, status = 'chapters_complete');

alter table public.chapters
  add column if not exists chapter_notes_status text;

update public.chapters
set chapter_notes_status = coalesce(chapter_notes_status, status);

-- Optional cleanup after the app is fully migrated:
-- alter table public.books drop column notes;
-- alter table public.chapters drop column status;
