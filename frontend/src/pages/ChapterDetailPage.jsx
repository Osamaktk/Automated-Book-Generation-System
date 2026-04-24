import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import EditorNotesHistory from "../components/shared/EditorNotesHistory";
import NotesPanels from "../components/shared/NotesPanels";
import Alert from "../components/ui/Alert";
import Loader from "../components/ui/Loader";
import StatusBadge from "../components/ui/StatusBadge";
import { useGuestSession } from "../context/GuestStorageContext";
import { useAuth } from "../hooks/useAuth";
import { useChapterDetail } from "../hooks/useChapterDetail";
import { submitChapterFeedback } from "../services/bookService";

function ChapterDetailPage() {
  const navigate = useNavigate();
  const { bookId, chapterId } = useParams();
  const { accessToken } = useAuth();
  const { submitChapterFeedback: submitGuestChapterFeedback } = useGuestSession();
  const { chapter, book, loading, error, reload, isGuestChapter } = useChapterDetail(bookId, chapterId);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [showRevision, setShowRevision] = useState(false);
  const [revisionNotes, setRevisionNotes] = useState("");
  const [message, setMessage] = useState(null);

  const historyItems = useMemo(
    () =>
      chapter?.editor_notes?.trim()
        ? [{ label: `Chapter ${chapter.chapter_number}`, text: chapter.editor_notes }]
        : [],
    [chapter]
  );

  async function handleFeedback(status) {
    if (status === "needs_revision" && !revisionNotes.trim()) {
      setMessage({ type: "error", text: "Please add editor feedback before requesting a revision." });
      return;
    }

    try {
      setFeedbackLoading(true);
      setMessage(null);
      const response = isGuestChapter
        ? submitGuestChapterFeedback(bookId, chapterId, { status, editor_notes: revisionNotes })
        : await submitChapterFeedback(chapterId, { status, editor_notes: revisionNotes }, accessToken);
      setMessage({ type: "success", text: response.message || "Chapter updated." });
      setShowRevision(false);
      setRevisionNotes("");
      await reload();
      setTimeout(() => navigate(`/books/${bookId}`), 1200);
    } catch (err) {
      setMessage({ type: "error", text: err.message || "Something went wrong." });
    } finally {
      setFeedbackLoading(false);
    }
  }

  if (loading) {
    return <Loader msg="Loading chapter..." />;
  }

  if (error || !chapter) {
    return <Alert type="error">{error || "Chapter not found."}</Alert>;
  }

  return (
    <div className="fade-up">
      <div className="back-btn" onClick={() => navigate(`/books/${bookId}`)}>
        Back to Book
      </div>

      {message ? <Alert type={message.type}>{message.text}</Alert> : null}

      <div className="page-header">
        <p className="eyebrow">Chapter {chapter.chapter_number}</p>
        <h2>Reading View</h2>
        <div className="top-status">
          <StatusBadge status={chapter.status} />
        </div>
        <div className="header-line" />
      </div>

      <div className="card">
        <div className="card-title">Chapter Notes</div>
        <NotesPanels
          beforeNotes={book?.notes || ""}
          afterNotes={chapter.editor_notes || ""}
          beforeLabel="Before Notes"
          afterLabel="After Notes"
        />
      </div>

      <div className="card">
        <div className="content-box chapter-content">{chapter.content}</div>
      </div>

      <div className="card">
        <div className="card-title">Editor Notes History</div>
        <EditorNotesHistory items={historyItems} emptyText="No editor notes yet for this chapter" />
      </div>

      {chapter.status === "approved" && chapter.summary ? (
        <div className="card">
          <div className="card-title">Chapter Summary</div>
          <div className="content-box summary-box">{chapter.summary}</div>
        </div>
      ) : null}

      {chapter.status === "waiting_for_review" ? (
        <div className="card">
          <div className="card-title">Editor Decision</div>
          <div className="inline-actions">
            <button className="btn btn-success" onClick={() => handleFeedback("approved")} disabled={feedbackLoading}>
              {feedbackLoading ? "Saving..." : "Approve Chapter"}
            </button>
            <button className="btn btn-gold" onClick={() => handleFeedback("final_chapter")} disabled={feedbackLoading}>
              {feedbackLoading ? "Saving..." : "Final Chapter"}
            </button>
            <button className="btn btn-ghost" onClick={() => setShowRevision((current) => !current)} disabled={feedbackLoading}>
              Request Revision
            </button>
          </div>

          {showRevision ? (
            <div className="mt-16">
              <textarea
                className="form-textarea"
                placeholder="Describe what needs to change in this chapter..."
                value={revisionNotes}
                onChange={(event) => setRevisionNotes(event.target.value)}
                disabled={feedbackLoading}
              />
              <button
                className="btn btn-danger mt-16"
                onClick={() => handleFeedback("needs_revision")}
                disabled={feedbackLoading || !revisionNotes.trim()}
              >
                {feedbackLoading ? "Sending..." : "Send for Revision"}
              </button>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export default ChapterDetailPage;
