import { useCallback, useEffect, useMemo, useState } from "react";

import { useGuestSession } from "../context/GuestStorageContext";
import { getBook, getBookChapters, getChapter } from "../services/bookService";
import { sortChapters } from "../utils/book";
import { useAuth } from "./useAuth";

export function useBookDetail(bookId) {
  const { accessToken, isAuthenticated } = useAuth();
  const { getBookDetail } = useGuestSession();
  const [data, setData] = useState(null);
  const [chapters, setChapters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [source, setSource] = useState("remote");

  const load = useCallback(
    async (withLoader = true) => {
      if (!bookId) {
        return;
      }

      const guestDetail = getBookDetail(bookId);
      if (guestDetail) {
        setData({ book: guestDetail.book, outline: guestDetail.outline });
        setChapters(guestDetail.chapters);
        setSource("guest");
        setError("");
        setLoading(false);
        return;
      }

      if (!isAuthenticated || !accessToken) {
        setData(null);
        setChapters([]);
        setSource("remote");
        setError("Sign in to load saved cloud books.");
        setLoading(false);
        return;
      }

      try {
        if (withLoader) {
          setLoading(true);
        }
        setError("");

        const [bookData, chapterData] = await Promise.all([
          getBook(bookId, accessToken),
          getBookChapters(bookId, accessToken).catch(() => ({ chapters: [] }))
        ]);

        const baseChapters = sortChapters(chapterData.chapters || []);
        const detailedChapters = await Promise.all(
          baseChapters.map(async (chapter) => {
            try {
              const detail = await getChapter(chapter.id, accessToken);
              return { ...chapter, ...detail.chapter };
            } catch {
              return chapter;
            }
          })
        );

        setData(bookData);
        setChapters(sortChapters(detailedChapters));
        setSource("remote");
      } catch (err) {
        setError(err.message || "Unable to load manuscript.");
      } finally {
        if (withLoader) {
          setLoading(false);
        }
      }
    },
    [accessToken, bookId, getBookDetail, isAuthenticated]
  );

  useEffect(() => {
    load(true);
  }, [load]);

  return useMemo(
    () => ({
      data,
      chapters,
      loading,
      error,
      source,
      isGuestBook: source === "guest",
      reload: load,
      setChapters
    }),
    [chapters, data, error, load, loading, source]
  );
}
