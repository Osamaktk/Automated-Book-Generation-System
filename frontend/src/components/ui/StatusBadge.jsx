const statusMap = {
  waiting_for_review: ["badge-review", "Awaiting Review"],
  approved: ["badge-approved", "Approved"],
  outline_approved: ["badge-approved", "Outline Approved"],
  chapters_in_progress: ["badge-progress", "In Progress"],
  chapters_complete: ["badge-complete", "Complete"],
  generating: ["badge-progress", "Generating"],
  needs_revision: ["badge-review", "Needs Revision"],
  waiting_for_input: ["badge-default", "Draft"]
};

function StatusBadge({ status }) {
  const [className, label] =
    statusMap[status] || ["badge-default", status ? status.replaceAll("_", " ") : "Unknown"];

  return (
    <span className={`badge ${className}`}>
      <span className="badge-dot" /> {label}
    </span>
  );
}

export default StatusBadge;
