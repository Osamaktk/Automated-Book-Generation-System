import { createContext, useContext, useMemo } from "react";

import { useGuestStorage } from "../hooks/useGuestStorage";
import {
  createGuestBookBundle,
  createGuestChapterBundle,
  regenerateGuestChapter,
  regenerateGuestOutline,
  sortChapters
} from "../utils/book";

const GuestStorageContext = createContext(null);

const EMPTY_STATE = {
  books: [],
  outlines: [],
  chapters: []
};

function updateGuestState(setState, updater) {
  setState((current) => {
    const nextState = updater(current);
    return nextState || current;
  });
}

export function GuestStorageProvider({ children }) {
  const [guestState, setGuestState, clearGuestState] = useGuestStorage(EMPTY_STATE);

  const value = useMemo(() => {
    function getBookDetail(bookId) {
      const book = guestState.books.find((item) => item.id === bookId) || null;
      if (!book) {
        return null;
      }

      const outline = guestState.outlines.find((item) => item.book_id === bookId) || null;
      const chapters = sortChapters(guestState.chapters.filter((item) => item.book_id === bookId));

      return { book, outline, chapters };
    }

    function createGuestBook(payload) {
      const bundle = createGuestBookBundle(payload);

      updateGuestState(setGuestState, (current) => ({
        books: [bundle.book, ...current.books],
        outlines: [bundle.outline, ...current.outlines],
        chapters: current.chapters
      }));

      return bundle;
    }

    function deleteGuestBook(bookId) {
      updateGuestState(setGuestState, (current) => ({
        books: current.books.filter((item) => item.id !== bookId),
        outlines: current.outlines.filter((item) => item.book_id !== bookId),
        chapters: current.chapters.filter((item) => item.book_id !== bookId)
      }));
    }

    function submitOutlineFeedback(bookId, payload) {
      const detail = getBookDetail(bookId);
      if (!detail?.book || !detail?.outline) {
        throw new Error("Guest book not found.");
      }

      const shouldGenerateFirstChapter =
        payload.status === "approved" && detail.chapters.length === 0;

      const nextOutline =
        payload.status === "needs_revision"
          ? regenerateGuestOutline(detail.book, detail.outline, payload.editor_notes || "")
          : { ...detail.outline, status: "approved", editor_notes: payload.editor_notes || "" };

      const nextChapter = shouldGenerateFirstChapter
        ? createGuestChapterBundle(
            { ...detail.book, status: "outline_approved" },
            nextOutline,
            detail.chapters
          )
        : null;

      const nextBookStatus =
        payload.status === "approved"
          ? nextChapter
            ? "chapters_in_progress"
            : "outline_approved"
          : "waiting_for_review";

      updateGuestState(setGuestState, (current) => ({
        books: current.books.map((item) =>
          item.id === bookId ? { ...item, status: nextBookStatus } : item
        ),
        outlines: current.outlines.map((item) => (item.id === nextOutline.id ? nextOutline : item)),
        chapters: nextChapter ? [...current.chapters, nextChapter] : current.chapters
      }));

      return {
        message:
          payload.status === "approved"
            ? nextChapter
              ? `Outline approved locally. Chapter ${nextChapter.chapter_number} was generated for review.`
              : "Outline approved locally."
            : "Outline revised locally and is ready for review."
      };
    }

    function generateGuestChapter(bookId) {
      const detail = getBookDetail(bookId);
      if (!detail?.book || !detail?.outline) {
        throw new Error("Guest book not found.");
      }

      const nextChapter = createGuestChapterBundle(detail.book, detail.outline, detail.chapters);

      updateGuestState(setGuestState, (current) => ({
        books: current.books.map((item) =>
          item.id === bookId
            ? {
                ...item,
                status: detail.book.status === "chapters_complete" ? "chapters_complete" : "chapters_in_progress"
              }
            : item
        ),
        outlines: current.outlines,
        chapters: [...current.chapters, nextChapter]
      }));

      return nextChapter;
    }

    function submitChapterFeedback(bookId, chapterId, payload) {
      const detail = getBookDetail(bookId);
      const chapter = detail?.chapters.find((item) => item.id === chapterId);

      if (!detail?.book || !chapter) {
        throw new Error("Guest chapter not found.");
      }

      let nextChapter = chapter;
      let nextBookStatus = detail.book.status;

      if (payload.status === "needs_revision") {
        nextChapter = regenerateGuestChapter(detail.book, detail.outline, chapter, payload.editor_notes || "");
      } else {
        nextChapter = {
          ...chapter,
          status: "approved",
          editor_notes: payload.editor_notes || chapter.editor_notes || ""
        };
        if (payload.status === "final_chapter") {
          nextBookStatus = "chapters_complete";
        }
      }

      updateGuestState(setGuestState, (current) => ({
        books: current.books.map((item) =>
          item.id === bookId ? { ...item, status: nextBookStatus } : item
        ),
        outlines: current.outlines,
        chapters: current.chapters.map((item) => (item.id === chapterId ? nextChapter : item))
      }));

      return {
        message:
          payload.status === "needs_revision"
            ? "Chapter revised locally and is ready for review."
            : "Chapter updated locally."
      };
    }

    function removeGuestBook(bookId) {
      deleteGuestBook(bookId);
    }

    return {
      guestState,
      guestBooks: guestState.books,
      getBookDetail,
      createGuestBook,
      deleteGuestBook,
      removeGuestBook,
      submitOutlineFeedback,
      generateGuestChapter,
      submitChapterFeedback,
      clearGuestState
    };
  }, [guestState, setGuestState, clearGuestState]);

  return <GuestStorageContext.Provider value={value}>{children}</GuestStorageContext.Provider>;
}

export function useGuestSession() {
  const value = useContext(GuestStorageContext);
  if (!value) {
    throw new Error("useGuestSession must be used inside GuestStorageProvider");
  }
  return value;
}
