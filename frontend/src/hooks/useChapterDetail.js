import { useCallback, useEffect, useState } from "react";

import { useGuestSession } from "../context/GuestStorageContext";
import { getBook, getChapter } from "../services/bookService";
import { useAuth } from "./useAuth";

export function useChapterDetail(bookId, chapterId) {
  const { accessToken, isAuthenticated } = useAuth();
  const { getBookDetail } = useGuestSession();
  const [chapter, setChapter] = useState(null);
  const [book, setBook] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [source, setSource] = useState("remote");

  const load = useCallback(async () => {
    if (!bookId || !chapterId) {
      return;
    }

    const guestDetail = getBookDetail(bookId);
    if (guestDetail) {
      setBook(guestDetail.book);
      setChapter(guestDetail.chapters.find((item) => item.id === chapterId) || null);
      setSource("guest");
      setError("");
      setLoading(false);
      return;
    }

    if (!isAuthenticated || !accessToken) {
      setLoading(false);
      setError("Sign in to load saved cloud chapters.");
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
      setSource("remote");
    } catch (err) {
      setError(err.message || "Unable to load chapter.");
    } finally {
      setLoading(false);
    }
  }, [accessToken, bookId, chapterId, getBookDetail, isAuthenticated]);

  useEffect(() => {
    load();
  }, [load]);

  return {
    chapter,
    book,
    loading,
    error,
    source,
    isGuestChapter: source === "guest",
    reload: load
  };
}
