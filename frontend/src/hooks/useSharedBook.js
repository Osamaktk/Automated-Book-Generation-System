import { useEffect, useState } from "react";

import { getSharedBook, getSharedBookChapters } from "../services/bookService";
import { sortChapters } from "../utils/book";

export function useSharedBook(bookId, shareToken) {
  const [data, setData] = useState(null);
  const [chapters, setChapters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        setLoading(true);
        setError("");
        const bookData = await getSharedBook(bookId, shareToken);
        const chapterData = await getSharedBookChapters(bookId, shareToken).catch(() => ({
          chapters: []
        }));

        if (active) {
          setData(bookData);
          setChapters(sortChapters(chapterData.chapters || []));
        }
      } catch (err) {
        if (active) {
          setError(err.message || "This shared link is invalid or has expired.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    if (bookId && shareToken) {
      load();
    } else {
      setLoading(false);
      setError("Missing shared book information.");
    }

    return () => {
      active = false;
    };
  }, [bookId, shareToken]);

  return {
    data,
    chapters,
    loading,
    error
  };
}
