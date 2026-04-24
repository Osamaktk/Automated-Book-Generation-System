export function sortChapters(chapters) {
  return [...chapters].sort((a, b) => a.chapter_number - b.chapter_number);
}

function createLocalId(prefix) {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function buildOutlinePoints(title, notes, editorNotes = "") {
  const rawParts = `${notes} ${editorNotes}`
    .split(/[.\n]/)
    .map((item) => item.trim())
    .filter(Boolean);

  const points = rawParts.slice(0, 5);
  while (points.length < 4) {
    points.push(`${title} thread ${points.length + 1}`);
  }
  return points;
}

export function createGuestBookBundle({ title, notes }) {
  const bookId = createLocalId("book");
  const outlineId = createLocalId("outline");
  const outlineContent = generateGuestOutline(title, notes);

  return {
    book: {
      id: bookId,
      title,
      notes,
      status: "waiting_for_review",
      created_at: new Date().toISOString(),
      source: "guest"
    },
    outline: {
      id: outlineId,
      book_id: bookId,
      content: outlineContent,
      status: "waiting_for_review",
      editor_notes: "",
      created_at: new Date().toISOString()
    }
  };
}

export function generateGuestOutline(title, notes, editorNotes = "") {
  const points = buildOutlinePoints(title, notes, editorNotes);
  return [
    `Title: ${title}`,
    "",
    "Working Outline",
    "",
    ...points.map((point, index) => `${index + 1}. ${point}`)
  ].join("\n");
}

export function regenerateGuestOutline(book, outline, editorNotes) {
  return {
    ...outline,
    content: generateGuestOutline(book.title, book.notes, editorNotes),
    status: "waiting_for_review",
    editor_notes: editorNotes
  };
}

function inferChapterTitle(outline, chapterNumber) {
  const lines = outline.content
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  const matched = lines.find((line) => line.startsWith(`${chapterNumber}.`));
  return matched ? matched.replace(/^\d+\.\s*/, "") : `Chapter ${chapterNumber}`;
}

export function createGuestChapterBundle(book, outline, chapters) {
  const chapterNumber = chapters.length + 1;
  const chapterTitle = inferChapterTitle(outline, chapterNumber);
  const previousSummary = chapters[chapters.length - 1]?.summary || "";
  const summary = `${chapterTitle} advances ${book.title} using the current outline and notes.`;
  const content = [
    `${chapterTitle}`,
    "",
    `This guest draft expands on the manuscript "${book.title}" using the author notes provided.`,
    previousSummary ? `It continues from the previous approved beat: ${previousSummary}` : "It opens the first major beat of the outline.",
    `Key direction: ${chapterTitle}.`,
    "",
    `Author notes reference: ${book.notes}`
  ].join("\n");

  return {
    id: createLocalId("chapter"),
    book_id: book.id,
    chapter_number: chapterNumber,
    content,
    summary,
    status: "waiting_for_review",
    editor_notes: "",
    created_at: new Date().toISOString()
  };
}

export function regenerateGuestChapter(book, outline, chapter, editorNotes) {
  return {
    ...chapter,
    content: [
      chapter.content,
      "",
      "Revision Notes Applied",
      editorNotes || "No editor notes supplied."
    ].join("\n"),
    status: "waiting_for_review",
    editor_notes: editorNotes,
    summary: `${chapter.summary} Revised with the latest editor notes for ${book.title}.`
  };
}

export function getPipelineStage(bookStatus, allChaptersApproved) {
  if (bookStatus === "chapters_complete" || allChaptersApproved) {
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
