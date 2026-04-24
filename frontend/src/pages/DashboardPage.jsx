import { useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import BookCard from "../components/books/BookCard";
import Alert from "../components/ui/Alert";
import Loader from "../components/ui/Loader";
import { useBooks } from "../hooks/useBooks";
import { createBookStream } from "../services/bookService";
import { isDraft } from "../utils/book";

function DashboardPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { books, loading, error, removeBook, reload } = useBooks();
  const [deletingId, setDeletingId] = useState("");
  const [message, setMessage] = useState(null);
  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [creating, setCreating] = useState(false);
  const [streaming, setStreaming] = useState("");

  const tab = searchParams.get("tab") === "create" ? "create" : "library";
  const filteredBooks = useMemo(() => books, [books]);
  const draftCount = useMemo(() => books.filter(isDraft).length, [books]);
  const completedCount = useMemo(() => books.length - draftCount, [books, draftCount]);

  async function handleDelete(bookId) {
    if (!window.confirm("Are you sure you want to discard this book? This cannot be undone.")) {
      return;
    }

    try {
      setDeletingId(bookId);
      await removeBook(bookId);
    } catch (err) {
      setMessage({ type: "error", text: err.message || "Failed to delete book." });
    } finally {
      setDeletingId("");
    }
  }

  async function handleCreate() {
    if (!title.trim() || !notes.trim()) {
      setMessage({ type: "error", text: "Please add both a title and author notes." });
      return;
    }

    try {
      setCreating(true);
      setStreaming("");
      setMessage(null);

      let nextBookId = null;

      await createBookStream({ title: title.trim(), notes: notes.trim() }, undefined, (event) => {
        if (event.type === "book_id") {
          nextBookId = event.book_id;
        }
        if (event.type === "chunk") {
          setStreaming((current) => current + event.text);
        }
        if (event.type === "done") {
          const resolvedBookId = nextBookId || event.book_id;
          if (resolvedBookId) {
            navigate(`/books/${resolvedBookId}`);
          }
        }
      });

      await reload();
    } catch (err) {
      setMessage({ type: "error", text: err.message || "Unable to generate outline." });
    } finally {
      setCreating(false);
    }
  }

  if (loading) {
    return <Loader msg="Loading library..." />;
  }

  return (
    <div className="fade-up">
      <div className="page-header">
        <h2>{tab === "create" ? "Create New Book" : "Library Dashboard"}</h2>
        <p>
          {tab === "create"
            ? "Turn a title and a brief into a review-ready outline."
            : "Manage your active manuscripts, reviews, and completed books."}
        </p>
        <div className="header-line" />
      </div>

      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-value">{books.length}</div>
          <div className="stat-label">Total Books</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{draftCount}</div>
          <div className="stat-label">In Progress</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{completedCount}</div>
          <div className="stat-label">Complete</div>
        </div>
      </div>

      {message ? <Alert type={message.type}>{message.text}</Alert> : null}
      {error ? <Alert type="error">{error}</Alert> : null}

      <div className="tab-switch">
        <button
          className={`tab-button ${tab === "library" ? "active" : ""}`}
          onClick={() => setSearchParams({})}
          type="button"
        >
          Library
        </button>
        <button
          className={`tab-button ${tab === "create" ? "active" : ""}`}
          onClick={() => setSearchParams({ tab: "create" })}
          type="button"
        >
          New Book
        </button>
      </div>

      {tab === "create" ? (
        <div className="card">
          <div className="card-title">Outline Generation</div>
          <div className="form-group">
            <label className="form-label">Book Title</label>
            <input
              className="form-input"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="The Lost City"
              disabled={creating}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Author Notes and Brief</label>
            <textarea
              className="form-textarea"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Story premise, themes, characters, tone, and constraints."
              disabled={creating}
            />
          </div>
          <div className="inline-actions">
            <button className="btn btn-gold" onClick={handleCreate} disabled={creating}>
              {creating ? "Generating..." : "Generate Outline"}
            </button>
            <button
              className="btn btn-ghost"
              onClick={() => {
                setTitle("");
                setNotes("");
                setStreaming("");
                setMessage(null);
              }}
              disabled={creating}
            >
              Reset
            </button>
          </div>

          {streaming ? (
            <div className="stream-box">
              <div className="stream-label">Live outline draft</div>
              <div className="content-box">{streaming}</div>
            </div>
          ) : null}
        </div>
      ) : filteredBooks.length ? (
        <div className="book-grid">
          {filteredBooks.map((book) => (
            <BookCard
              key={book.id}
              book={book}
              deleting={deletingId === book.id}
              onDelete={handleDelete}
              onOpen={(id) => navigate(`/books/${id}`)}
            />
          ))}
        </div>
      ) : (
        <div className="card empty-state">
          <div className="empty-icon">AB</div>
          <h3>Your library is empty</h3>
          <p>Start your first manuscript to begin the editorial workflow.</p>
          <button className="btn btn-gold" onClick={() => setSearchParams({ tab: "create" })}>
            Start Writing
          </button>
        </div>
      )}
    </div>
  );
}

export default DashboardPage;
