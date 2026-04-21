# 📘 AutoBook — Milestone 1

Automated book generation system with human-in-the-loop review.

## 🚀 Deploy to Railway

1. Push this folder to a GitHub repo
2. Go to railway.app → New Project → Deploy from GitHub
3. Select your repo
4. Go to Variables tab and add:
   - SUPABASE_URL
   - SUPABASE_KEY
   - DEEPSEEK_API_KEY
5. Railway auto-deploys and gives you a live URL!

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | / | Health check |
| POST | /books/create | Create book + generate outline |
| GET  | /books | List all books |
| GET  | /books/{id} | Get book + outline |
| POST | /books/{id}/feedback | Editor approves or requests revision |

## 🧪 Test It (after deployment)

### Create a book:
```
POST /books/create
{
  "title": "The Lost City",
  "notes": "A thriller about an archaeologist who discovers a hidden civilization in the Amazon jungle."
}
```

### Approve the outline:
```
POST /books/{book_id}/feedback
{
  "status": "approved",
  "editor_notes": ""
}
```

### Request revision:
```
POST /books/{book_id}/feedback
{
  "status": "needs_revision",
  "editor_notes": "Add more mystery elements and make chapter 3 about a chase scene."
}
```
