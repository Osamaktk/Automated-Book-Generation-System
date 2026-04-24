function EditorNotesHistory({ items, emptyText }) {
  if (!items?.length) {
    return (
      <div className="empty-state">
        <p>{emptyText}</p>
      </div>
    );
  }

  return (
    <div className="history-list">
      {items.map((item) => (
        <div key={`${item.label}-${item.text}`} className="history-item card">
          <div className="meta-panel-label">{item.label}</div>
          <div className="content-box">{item.text}</div>
        </div>
      ))}
    </div>
  );
}

export default EditorNotesHistory;
