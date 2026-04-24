function NotesPanels({
  beforeNotes,
  afterNotes,
  beforeLabel = "Before Notes",
  afterLabel = "After Notes"
}) {
  return (
    <div className="panel-grid">
      <div className="meta-panel">
        <div className="card">
          <div className="meta-panel-label">{beforeLabel}</div>
          <div className="meta-panel-body content-box">{beforeNotes || "No notes added."}</div>
        </div>
      </div>
      <div className="meta-panel">
        <div className="card">
          <div className="meta-panel-label">{afterLabel}</div>
          <div className="meta-panel-body content-box">{afterNotes || "No notes yet."}</div>
        </div>
      </div>
    </div>
  );
}

export default NotesPanels;
