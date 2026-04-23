import { useCallback, useEffect, useState } from "react";

import { deleteBook, getBooks } from "../services/bookService";
import { useAuth } from "./useAuth";

export function useBooks() {
  const { accessToken } = useAuth();
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadBooks = useCallback(async () => {
    try {
      setLoading(true);
      setError("");
      const data = await getBooks(accessToken);
      setBooks(data.books || []);
    } catch (err) {
      setError(err.message || "Unable to load books.");
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    loadBooks();
  }, [loadBooks]);

  const removeBook = useCallback(
    async (bookId) => {
      await deleteBook(bookId, accessToken);
      setBooks((current) => current.filter((book) => book.id !== bookId));
    },
    [accessToken]
  );

  return {
    books,
    loading,
    error,
    reload: loadBooks,
    removeBook
  };
}
