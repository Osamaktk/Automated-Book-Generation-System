function EditorNotesHistory({ items, emptyText = "No editor notes yet" }) {
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
        <div className="history-item" key={`${item.label}-${item.text}`}>
          <div className="history-title">{item.label}</div>
          <div className="meta-panel-body">{item.text}</div>
        </div>
      ))}
    </div>
  );
}

export default EditorNotesHistory;
