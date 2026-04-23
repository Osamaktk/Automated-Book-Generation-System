# AutoBook Frontend

This frontend is a modular Vite + React version of the original single-file `index.html`.

## Stack

- React
- Vite
- React Router
- Supabase Auth

## Project Structure

```text
frontend/
  public/
  src/
    components/
      books/
      layout/
      shared/
      ui/
    context/
    hooks/
    pages/
    services/
    styles/
    utils/
  .env.example
  index.html
  package.json
  vite.config.js
```

## Environment Variables

Create a `.env` file in `frontend/` and copy these values:

```env
VITE_API_URL=http://127.0.0.1:8000
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

## Local Development

1. Open the `frontend/` folder in VS Code.
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

- Authenticated API requests automatically send `Authorization: Bearer <access_token>`.
- Shared read-only views support both `token` and `share` query params for compatibility with backend share links.
- Download requests for compiled books use authenticated `fetch` so protected file downloads still work.
