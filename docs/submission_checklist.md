# Submission Checklist

Use this file to prepare the final non-code deliverables required by the project brief.

## 1. Final Deliverables

- Clean project repository
- Database schema description or visual
- Dashboard screenshots or live URL
- Video demonstration
- Sample generated manuscript in `docx` or `pdf`

## 2. What Is Already Done

- Gated outline generation
- Human-in-the-loop outline review
- Sequential chapter generation
- Context chaining with chapter summaries
- Monitoring dashboard
- Email notifications
- Final manuscript compilation
- Spreadsheet import for local Excel / exported Google Sheets
- Brief-style field alignment in API and UI

## 3. Screenshot List

Capture these screenshots for the submission package:

1. Library dashboard
- Show the book list and progress cards

2. Create new book view
- Show title + notes entry before generation

3. Outline review view
- Show generated outline with approve / revision actions

4. Chapter review view
- Show chapter content, `chapter_notes_status`, and approval actions

5. Completion view
- Show `no_notes_needed = true` and final manuscript ready state

6. Export view
- Show `docx` and `pdf` download options

7. Notification proof
- Show the email notification in Gmail

## 4. Demo Checklist

Run this flow during your final recording:

1. Open the dashboard
2. Create a new book or import one from spreadsheet
3. Show the generated outline
4. Approve the outline or request one revision
5. Show chapter generation starting
6. Approve a chapter and explain summary/context chaining
7. Approve the remaining planned chapters
8. Show that the book auto-completes
9. Show the notification email
10. Export the final manuscript as `docx` or `pdf`

## 5. Short Video Script

Use this as a simple speaking script:

1. Introduction
- "This is my Automated Book Generation System built around a human-in-the-loop editorial workflow."

2. Input and Outline
- "The process starts with a title and initial notes, or spreadsheet import."
- "The AI generates an outline, but it does not continue automatically. The editor must review it first."

3. Human Review
- "Here the editor can approve the outline or request revision notes."
- "This matches the gated workflow in the project brief."

4. Chapter Engine
- "After approval, chapters are generated sequentially."
- "Each approved chapter is summarized and used as context for the next chapter to reduce narrative drift."

5. Monitoring Dashboard
- "The dashboard shows project progress, outline state, chapter review state, and the brief-style fields required by the project."

6. Notifications
- "When review is needed or the manuscript is complete, the system sends email notifications."

7. Final Compilation
- "Once all planned chapters are approved, the system marks the manuscript complete and enables final export as PDF or DOCX."

8. Close
- "This completes the title-to-manuscript workflow described in the project brief."

## 6. Suggested Folder for Submission Assets

Create a simple folder like this in your project root before final submission:

```text
submission/
  screenshots/
  sample-output/
  demo-notes/
```

Recommended contents:

- `submission/screenshots/dashboard-library.png`
- `submission/screenshots/create-book.png`
- `submission/screenshots/outline-review.png`
- `submission/screenshots/chapter-review.png`
- `submission/screenshots/final-export.png`
- `submission/screenshots/email-notification.png`
- `submission/sample-output/sample-manuscript.docx`
- `submission/demo-notes/video-script.txt`
