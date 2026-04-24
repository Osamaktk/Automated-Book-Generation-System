import { useCallback, useEffect, useState } from "react";

import { deleteBook, getBooks } from "../services/bookService";

export function useBooks() {
  const [remoteBooks, setRemoteBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadBooks = useCallback(async () => {
    try {
      setLoading(true);
      setError("");
      const data = await getBooks();
      setRemoteBooks(data.books || []);
    } catch (err) {
      setError(err.message || "Unable to load books.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadBooks();
  }, [loadBooks]);

  const removeBook = useCallback(
    async (bookId) => {
      await deleteBook(bookId);
      setRemoteBooks((current) => current.filter((book) => book.id !== bookId));
    },
    []
  );

  return {
    books: remoteBooks,
    loading,
    error,
    reload: loadBooks,
    removeBook
  };
}
