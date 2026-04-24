# AutoBook Frontend

This frontend is a modular Vite + React app for the FastAPI + Supabase backend.

## Folder Structure

```text
frontend/
  src/
    components/
      books/
      layout/
      shared/
      ui/
    context/
    hooks/
    lib/
    pages/
    services/
    utils/
    App.jsx
    index.css
    main.jsx
  .env
  .env.example
  package.json
```

## Environment Variables

Set these in `frontend/.env`:

```env
VITE_API_URL=http://127.0.0.1:8000
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

## Local Development

1. Open `frontend/` in VS Code.
2. Run `npm install`
3. Run `npm run dev`
4. Open the local Vite URL shown in the terminal.

## Routes

- `/login`
- `/dashboard`
- `/books/:bookId`
- `/books/:bookId/chapters/:chapterId`
- `/shared?book=<book_id>&token=<share_token>`

## Notes

- All authenticated API requests attach `Authorization: Bearer <access_token>`.
- Shared links support both `token` and `share` query params.
- File downloads use authenticated fetch requests so protected compile endpoints still work.
