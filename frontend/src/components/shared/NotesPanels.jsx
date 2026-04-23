function NotesPanels({
  beforeNotes,
  afterNotes,
  beforeLabel = "Before Notes",
  afterLabel = "After Notes"
}) {
  return (
    <div className="panel-grid">
      <div className="meta-panel">
        <div className="meta-panel-label">{beforeLabel}</div>
        <div className="meta-panel-body">{beforeNotes || "No notes available."}</div>
      </div>
      <div className="meta-panel">
        <div className="meta-panel-label">{afterLabel}</div>
        <div className="meta-panel-body">{afterNotes || "No editor notes yet."}</div>
      </div>
    </div>
  );
}

export default NotesPanels;
