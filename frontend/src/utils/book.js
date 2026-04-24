export function sortChapters(chapters) {
  return [...chapters].sort((a, b) => a.chapter_number - b.chapter_number);
}

export function getPipelineStage(bookStatus) {
  if (bookStatus === "chapters_complete") {
    return "final";
  }
  if (bookStatus === "outline_approved" || bookStatus === "chapters_in_progress") {
    return "chapters";
  }
  return "outline";
}

export function getBookNotifications(book, outline, chapters) {
  const notifications = [];
  const pendingChapter = chapters.find((chapter) => chapter.status === "waiting_for_review");

  if (book?.status === "chapters_complete") {
    notifications.push({ type: "success", text: "Book completed" });
  } else if (pendingChapter) {
    notifications.push({
      type: "info",
      text: `Chapter ${pendingChapter.chapter_number} waiting for approval`
    });
  } else if (outline?.status === "waiting_for_review" || book?.status === "waiting_for_review") {
    notifications.push({ type: "info", text: "Outline needs review" });
  }

  return notifications;
}

export function isDraft(book) {
  return ["generating", "waiting_for_review", "outline_approved", "chapters_in_progress"].includes(
    book.status
  );
}
