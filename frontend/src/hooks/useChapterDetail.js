import { useCallback, useEffect, useState } from "react";

import { getBook, getChapter } from "../services/bookService";
import { useAuth } from "./useAuth";

export function useChapterDetail(bookId, chapterId) {
  const { accessToken } = useAuth();
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
        getChapter(chapterId, accessToken),
        getBook(bookId, accessToken).catch(() => null)
      ]);
      setChapter(chapterResponse.chapter);
      setBook(bookResponse?.book || null);
    } catch (err) {
      setError(err.message || "Unable to load chapter.");
    } finally {
      setLoading(false);
    }
  }, [accessToken, bookId, chapterId]);

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
