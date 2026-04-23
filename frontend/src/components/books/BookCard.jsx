import StatusBadge from "../ui/StatusBadge";

function BookCard({ book, onOpen, onDelete, deleting }) {
  return (
    <div className="book-card" onClick={() => onOpen(book.id)}>
      <div className="book-card-spine" />
      <div className="book-card-inner">
        <div className="book-card-number">Manuscript</div>
        <div className="book-title">{book.title}</div>
        <div className="book-notes">{book.notes}</div>
      </div>
      <div className="book-card-footer">
        <StatusBadge status={book.status} />
        <div className="inline-actions">
          <button
            className="btn btn-ghost btn-sm"
            onClick={(event) => {
              event.stopPropagation();
              onDelete(book.id);
            }}
            disabled={deleting}
            type="button"
          >
            {deleting ? "Removing..." : "Delete"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default BookCard;
