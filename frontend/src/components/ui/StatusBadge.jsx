const STATUS_MAP = {
  waiting_for_review: { label: "Waiting", className: "badge-review" },
  approved: { label: "Approved", className: "badge-approved" },
  outline_approved: { label: "Outline Approved", className: "badge-approved" },
  chapters_in_progress: { label: "In Progress", className: "badge-progress" },
  chapters_complete: { label: "Complete", className: "badge-complete" },
  generating: { label: "Generating", className: "badge-progress" },
  needs_revision: { label: "Needs Revision", className: "badge-review" }
};

function StatusBadge({ status }) {
  const meta = STATUS_MAP[status] || {
    label: (status || "unknown").replaceAll("_", " "),
    className: "badge-default"
  };

  return (
    <span className={`badge ${meta.className}`}>
      <span className="badge-dot" />
      {meta.label}
    </span>
  );
}

export default StatusBadge;
