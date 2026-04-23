import { useCallback, useEffect, useMemo, useState } from "react";

import { getBook, getBookChapters, getChapter } from "../services/bookService";
import { sortChapters } from "../utils/book";
import { useAuth } from "./useAuth";

export function useBookDetail(bookId) {
  const { accessToken } = useAuth();
  const [data, setData] = useState(null);
  const [chapters, setChapters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(
    async (withLoader = true) => {
      if (!bookId) {
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
      } catch (err) {
        setError(err.message || "Unable to load manuscript.");
      } finally {
        if (withLoader) {
          setLoading(false);
        }
      }
    },
    [accessToken, bookId]
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
      reload: load,
      setChapters
    }),
    [chapters, data, error, load, loading]
  );
}
