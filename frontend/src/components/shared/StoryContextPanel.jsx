function StoryContextPanel({ chapters }) {
  return (
    <div className="card">
      <div className="card-title">Story Context</div>
      {chapters?.length ? (
        <div className="context-list">
          {chapters.map((chapter) => (
            <div key={chapter.id} className="context-item card">
              <div className="meta-panel-label">Chapter {chapter.chapter_number}</div>
              <div className="content-box">{chapter.summary}</div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <p>Approved chapter summaries will appear here to show narrative continuity.</p>
        </div>
      )}
    </div>
  );
}

export default StoryContextPanel;
