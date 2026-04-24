import { useCallback, useEffect, useState } from "react";

import { getBook, getChapter } from "../services/bookService";

export function useChapterDetail(bookId, chapterId) {
  const [chapter, setChapter] = useState(null);
  const [book, setBook] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!bookId || !chapterId) {
      return;
    }

    try {
      setLoading(true);
      setError("");
      const [chapterResponse, bookResponse] = await Promise.all([
        getChapter(chapterId),
        getBook(bookId).catch(() => null)
      ]);
      setChapter(chapterResponse.chapter);
      setBook(bookResponse?.book || null);
    } catch (err) {
      setError(err.message || "Unable to load chapter.");
    } finally {
      setLoading(false);
    }
  }, [bookId, chapterId]);

  useEffect(() => {
    load();
  }, [load]);

  return {
    chapter,
    book,
    loading,
    error,
    reload: load
  };
}
