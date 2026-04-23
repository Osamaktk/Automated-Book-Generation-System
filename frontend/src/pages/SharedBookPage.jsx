import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";

import Alert from "../components/ui/Alert";
import Loader from "../components/ui/Loader";
import StatusBadge from "../components/ui/StatusBadge";
import { useSharedBook } from "../hooks/useSharedBook";

function SharedBookPage() {
  const [searchParams] = useSearchParams();
  const shareToken = searchParams.get("token") || searchParams.get("share");
  const bookId = searchParams.get("book") || searchParams.get("id");
  const { data, chapters, loading, error } = useSharedBook(bookId, shareToken);

  const book = data?.book;
  const outline = data?.outline;
  const chapterCountLabel = useMemo(
    () => `${chapters.length} chapter${chapters.length === 1 ? "" : "s"}`,
    [chapters.length]
  );

  if (loading) {
    return (
      <div className="center-screen">
        <Loader msg="Loading shared book..." />
      </div>
    );
  }

  if (error || !book) {
    return (
      <div className="center-screen">
        <Alert type="error">{error || "This shared link is invalid or has expired."}</Alert>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <nav className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-icon">AB</div>
          <h1>AutoBook</h1>
          <p>Shared Preview</p>
        </div>
        <div className="sidebar-footer">
          <p>Read-only shared view</p>
        </div>
      </nav>

      <main className="main">
        <div className="fade-up">
          <div className="share-banner">Shared read-only view</div>

          <div className="page-header">
            <h2>{book.title}</h2>
            <p>{chapterCountLabel}</p>
            <div className="header-line" />
          </div>

          {outline ? (
            <div className="card">
              <div className="card-title">Book Outline</div>
              <div className="content-box">{outline.content}</div>
            </div>
          ) : null}

          {chapters.length ? (
            <div className="card">
              <div className="card-title">Chapters</div>
              {chapters.map((chapter) => (
                <div key={chapter.id} className="chapter-item chapter-item-static">
                  <span className="chapter-num">Chapter {chapter.chapter_number}</span>
                  <StatusBadge status={chapter.status} />
                </div>
              ))}
            </div>
          ) : null}
        </div>
      </main>
    </div>
  );
}

export default SharedBookPage;
