import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import EditorNotesHistory from "../components/shared/EditorNotesHistory";
import NotesPanels from "../components/shared/NotesPanels";
import NotificationBanner from "../components/shared/NotificationBanner";
import Pipeline from "../components/shared/Pipeline";
import StoryContextPanel from "../components/shared/StoryContextPanel";
import Alert from "../components/ui/Alert";
import Loader from "../components/ui/Loader";
import StatusBadge from "../components/ui/StatusBadge";
import { useBookDetail } from "../hooks/useBookDetail";
import {
  downloadCompiledBook,
  generateChapterStream,
  getBookOutlines,
  submitOutlineFeedback
} from "../services/bookService";
import { getBookNotifications, getPipelineStage } from "../utils/book";

function BookDetailPage() {
  const navigate = useNavigate();
  const { bookId } = useParams();
  const { data, chapters, loading, error, reload } = useBookDetail(bookId);
  const [revNotes, setRevNotes] = useState("");
  const [showRev, setShowRev] = useState(false);
  const [message, setMessage] = useState(null);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [streamText, setStreamText] = useState("");
  const [downloadingFormat, setDownloadingFormat] = useState("");
  const [showOutlineHistory, setShowOutlineHistory] = useState(false);
  const [outlineHistory, setOutlineHistory] = useState([]);
  const [outlineHistoryLoading, setOutlineHistoryLoading] = useState(false);

  const book = data?.book;
  const outline = data?.outline;
  const plannedChapterCount = book?.planned_chapter_count || 0;

  const approvedCount = useMemo(
    () => chapters.filter((chapter) => chapter.status === "approved").length,
    [chapters]
  );
  const chaptersWithWordCount = useMemo(
    () =>
      chapters.map((chapter) => ({
        ...chapter,
        wordCount: (chapter.content || "").trim().split(/\s+/).filter(Boolean).length
      })),
    [chapters]
  );
  const pendingChapter = useMemo(
    () => chaptersWithWordCount.find((chapter) => chapter.status === "waiting_for_review"),
    [chaptersWithWordCount]
  );
  const allChaptersApproved = useMemo(
    () =>
      plannedChapterCount > 0
        ? approvedCount >= plannedChapterCount
        : chaptersWithWordCount.length > 0 &&
          chaptersWithWordCount.every((chapter) => chapter.status === "approved"),
    [approvedCount, chaptersWithWordCount, plannedChapterCount]
  );
  const outlineHistoryItems = useMemo(
    () =>
      [...outlineHistory]
        .sort((left, right) => {
          const leftTime = new Date(left.created_at || 0).getTime();
          const rightTime = new Date(right.created_at || 0).getTime();
          return leftTime - rightTime;
        })
        .filter((item) => item.editor_notes && item.editor_notes.trim())
        .map((item, index) => ({
          label: item.created_at
            ? `Revision ${index + 1} - ${new Date(item.created_at).toLocaleDateString()}`
            : `Revision ${index + 1}`,
          text: item.editor_notes
        })),
    [outlineHistory]
  );
  const isComplete = book?.status === "chapters_complete";
  const outlineApproved =
    outline?.status === "approved" ||
    ["outline_approved", "chapters_in_progress", "chapters_complete"].includes(book?.status);
  const stage = getPipelineStage(book?.status);
  const notifications = getBookNotifications(book, outline, chapters);

  async function handleOutlineFeedback(status) {
    if (status === "needs_revision" && !revNotes.trim()) {
      setMessage({ type: "error", text: "Please add editor feedback before requesting a revision." });
      return;
    }

    try {
      setFeedbackLoading(true);
      setMessage(null);
      const response = await submitOutlineFeedback(bookId, { status, editor_notes: revNotes });
      setMessage({ type: "success", text: response.message || "Outline updated." });
      setShowRev(false);
      setRevNotes("");
      await reload(false);
    } catch (err) {
      setMessage({ type: "error", text: err.message || "Unable to update outline." });
    } finally {
      setFeedbackLoading(false);
    }
  }

  async function handleGenerateChapter() {
    try {
      setGenerating(true);
      setStreamText("");
      setMessage(null);

      await generateChapterStream(bookId, undefined, async (event) => {
        if (event.type === "chunk") {
          setStreamText((current) => current + event.text);
        }
        if (event.type === "chapter_info") {
          setMessage({ type: "info", text: `Writing ${event.chapter_title}` });
        }
        if (event.type === "done") {
          setGenerating(false);
          setStreamText("");
          await reload(false);
          setMessage({
            type: "success",
            text: `Chapter ${event.chapter_number} ready for review.`
          });
        }
      });
    } catch (err) {
      setMessage({ type: "error", text: err.message || "Connection error." });
      setGenerating(false);
    }
  }

  async function handleDownload(format) {
    try {
      setDownloadingFormat(format);
      const { blob, filename } = await downloadCompiledBook(bookId, format);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setMessage({ type: "success", text: `Downloaded ${filename}` });
    } catch (err) {
      setMessage({ type: "error", text: err.message || "Unable to download manuscript." });
    } finally {
      setDownloadingFormat("");
    }
  }

  async function fetchOutlineHistory() {
    if (!bookId || !outline) {
      setOutlineHistory([]);
      return;
    }

    setOutlineHistoryLoading(true);
    try {
      try {
        const response = await getBookOutlines(bookId);
        const outlines = Array.isArray(response?.outlines) ? response.outlines : [];
        if (outlines.length) {
          setOutlineHistory(outlines);
          return;
        }
      } catch {
        // Silently fall back to the current outline when history is unavailable.
      }

      setOutlineHistory([outline]);
    } finally {
      setOutlineHistoryLoading(false);
    }
  }

  useEffect(() => {
    if (showOutlineHistory) {
      fetchOutlineHistory();
    }
  }, [showOutlineHistory, bookId, outline]);

  if (loading) {
    return <Loader msg="Loading manuscript..." />;
  }

  if (error || !book) {
    return <Alert type="error">{error || "Book not found."}</Alert>;
  }

  const chapterHistory = chaptersWithWordCount
    .filter((chapter) => chapter.editor_notes && chapter.editor_notes.trim())
    .map((chapter) => ({
      label: `Chapter ${chapter.chapter_number}`,
      text: chapter.editor_notes
    }));

  const canGenerate =
    outlineApproved &&
    !pendingChapter &&
    !isComplete &&
    !generating &&
    !feedbackLoading &&
    (plannedChapterCount === 0 || approvedCount < plannedChapterCount);
  const progressPercent = plannedChapterCount
    ? Math.min(100, Math.round((approvedCount / plannedChapterCount) * 100))
    : chapters.length
      ? Math.round((approvedCount / chapters.length) * 100)
      : 0;

  return (
    <div className="fade-up">
      <div className="top-actions">
        <button className="btn btn-ghost" onClick={() => navigate("/dashboard")} type="button">
          Dashboard
        </button>
        <button
          className="btn btn-gold"
          onClick={() => navigate("/dashboard?tab=create")}
          type="button"
        >
          New Book
        </button>
      </div>

      {message ? <Alert type={message.type}>{message.text}</Alert> : null}
      <NotificationBanner items={notifications} />
      <Pipeline stage={stage} />

      <div className="flex-between page-header">
        <div>
          <h2>{book.title}</h2>
          <div className="top-status">
            <StatusBadge status={book.status} />
          </div>
          <p className="page-subcopy">
            Review the outline, guide revisions, and publish the final manuscript once the planned
            chapters are approved.
          </p>
          <div className="header-line" />
        </div>
      </div>

      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-value">{plannedChapterCount || chapters.length}</div>
          <div className="stat-label">{plannedChapterCount ? "Planned" : "Generated"}</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{approvedCount}</div>
          <div className="stat-label">Approved</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{progressPercent}%</div>
          <div className="stat-label">Complete</div>
        </div>
      </div>

      <div className="card compact-card">
        <div className="progress-label">
          <span>MANUSCRIPT PROGRESS</span>
          <span>
            {approvedCount} of {plannedChapterCount || chapters.length} chapters approved
          </span>
        </div>
        <div className="progress-wrap">
          <div className="progress-fill" style={{ width: `${progressPercent}%` }} />
        </div>
      </div>

      <div className="card">
        <div className="card-title">Editorial Notes</div>
        <NotesPanels beforeNotes={book.notes} afterNotes={outline?.editor_notes || ""} />
      </div>

      <div className="card">
        <div className="card-title">Project Brief Fields</div>
        <div className="brief-grid">
          <div className="brief-field">
            <div className="meta-panel-label">notes_on_outline_before</div>
            <div className="content-box brief-value">{book.notes_on_outline_before || "No notes added."}</div>
          </div>
          <div className="brief-field">
            <div className="meta-panel-label">status_outline_notes</div>
            <div className="content-box brief-value">{book.status_outline_notes || "not_started"}</div>
          </div>
          <div className="brief-field">
            <div className="meta-panel-label">planned_chapter_count</div>
            <div className="content-box brief-value">{String(plannedChapterCount || 0)}</div>
          </div>
          <div className="brief-field">
            <div className="meta-panel-label">no_notes_needed</div>
            <div className="content-box brief-value">{book.no_notes_needed ? "true" : "false"}</div>
          </div>
        </div>
      </div>

      {outline ? (
        <div className="card">
          <div className="section-header">
            <div className="card-title">Book Outline</div>
            <div className="flex align-center">
              <StatusBadge status={outline.status} />
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => setShowOutlineHistory((current) => !current)}
                type="button"
              >
                {showOutlineHistory ? "Hide revision history" : "View revision history"}
              </button>
            </div>
          </div>
          <div className="content-box">{outline.content}</div>

          {showOutlineHistory ? (
            <div className="mt-16">
              <div className="card compact-card">
                <div className="card-title">Outline Revision History</div>
                {outlineHistoryLoading ? (
                  <div className="helper-text">Loading revision history...</div>
                ) : (
                  <EditorNotesHistory
                    items={outlineHistoryItems}
                    emptyText="No outline revision notes yet"
                  />
                )}
              </div>
            </div>
          ) : null}

          {outline.status === "waiting_for_review" ? (
            <div className="mt-24">
              <div className="inline-actions">
                <button
                  className="btn btn-success"
                  onClick={() => handleOutlineFeedback("approved")}
                  disabled={feedbackLoading || generating}
                >
                  Approve Outline
                </button>
                <button
                  className="btn btn-ghost"
                  onClick={() => setShowRev((current) => !current)}
                  disabled={feedbackLoading || generating}
                >
                  Request Revision
                </button>
              </div>

              {showRev ? (
                <div className="mt-16">
                  <textarea
                    className="form-textarea"
                    placeholder="Describe what needs to change..."
                    value={revNotes}
                    onChange={(event) => setRevNotes(event.target.value)}
                  />
                  <button
                    className="btn btn-danger mt-16"
                    onClick={() => handleOutlineFeedback("needs_revision")}
                    disabled={feedbackLoading || !revNotes.trim()}
                  >
                    {feedbackLoading ? "Sending..." : "Send Revision Request"}
                  </button>
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      ) : null}

      <StoryContextPanel chapters={chapters.filter((chapter) => chapter.summary)} />

      <div className="card">
        <div className="card-title">Editor Notes History</div>
        <EditorNotesHistory items={chapterHistory} emptyText="No chapter feedback history yet" />
      </div>

      {(outlineApproved || isComplete || chaptersWithWordCount.length > 0) ? (
        <div className="card">
          <div className="section-header">
            <div className="card-title">Chapters</div>
            {!isComplete ? (
              <button className="btn btn-gold btn-sm" onClick={handleGenerateChapter} disabled={!canGenerate}>
                {generating ? "Writing..." : pendingChapter ? "Pending Review" : "Next Chapter"}
              </button>
            ) : null}
          </div>

          <div className="helper-text">
            {!outlineApproved
              ? "Outline must be approved before chapter generation can begin."
              : pendingChapter
                ? `Approve Chapter ${pendingChapter.chapter_number} before generating the next chapter.`
                : isComplete
                  ? "This book has already been completed. Download options are available below."
                  : plannedChapterCount
                    ? `Generate the next chapter in sequence. Planned total: ${plannedChapterCount}.`
                    : "Generate the next chapter in sequence."}
          </div>

          {isComplete ? (
            <div className="download-panel">
              <div className="download-panel-label">Download Final Manuscript</div>
              <div className="download-btns">
                {["docx", "pdf", "txt"].map((format) => (
                  <button
                    key={format}
                    className="btn-download"
                    onClick={() => handleDownload(format)}
                    disabled={Boolean(downloadingFormat)}
                  >
                    {downloadingFormat === format ? "Downloading..." : format.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {generating && streamText ? (
            <div className="stream-box">
              <div className="stream-label">AI is writing...</div>
              <div className="content-box">{streamText}</div>
            </div>
          ) : null}

          {chaptersWithWordCount.length ? (
            chaptersWithWordCount.map((chapter) => (
              <Link key={chapter.id} className="chapter-item link-reset" to={`/books/${bookId}/chapters/${chapter.id}`}>
                <div className="flex align-center">
                  <span className="chapter-num">Chapter {chapter.chapter_number}</span>
                  <StatusBadge status={chapter.status} />
                  {chapter.content ? (
                    <span className="helper-text" style={{ marginLeft: "0.75rem" }}>
                      ~{chapter.wordCount.toLocaleString()} words
                    </span>
                  ) : null}
                </div>
                <span className="chapter-arrow">Read</span>
              </Link>
            ))
          ) : (
            <div className="empty-state compact-empty">
              <p>Approve the outline, then generate your first chapter.</p>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}

export default BookDetailPage;
