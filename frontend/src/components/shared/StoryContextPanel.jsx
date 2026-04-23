function StoryContextPanel({ chapters }) {
  return (
    <div className="card">
      <div className="card-title">Story Context</div>
      {chapters?.length ? (
        <div className="context-list">
          {chapters.map((chapter) => (
            <div className="context-item" key={chapter.id}>
              <div className="chapter-meta-title">Chapter {chapter.chapter_number}</div>
              <div className="meta-panel-body">{chapter.summary}</div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <p>No chapter summaries yet.</p>
        </div>
      )}
    </div>
  );
}

export default StoryContextPanel;
