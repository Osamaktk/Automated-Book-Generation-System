import { useCallback, useEffect, useState } from "react";

import { useGuestSession } from "../context/GuestStorageContext";
import { deleteBook, getBooks } from "../services/bookService";
import { useAuth } from "./useAuth";

export function useBooks() {
  const { accessToken, isAuthenticated } = useAuth();
  const { guestBooks, removeGuestBook } = useGuestSession();
  const [remoteBooks, setRemoteBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadBooks = useCallback(async () => {
    if (!isAuthenticated || !accessToken) {
      setRemoteBooks([]);
      setLoading(false);
      setError("");
      return;
    }

    try {
      setLoading(true);
      setError("");
      const data = await getBooks(accessToken);
      setRemoteBooks(data.books || []);
    } catch (err) {
      setError(err.message || "Unable to load books.");
    } finally {
      setLoading(false);
    }
  }, [accessToken, isAuthenticated]);

  useEffect(() => {
    loadBooks();
  }, [loadBooks]);

  const removeBook = useCallback(
    async (bookId) => {
      const guestBook = guestBooks.find((book) => book.id === bookId);
      if (guestBook) {
        removeGuestBook(bookId);
        return;
      }

      await deleteBook(bookId, accessToken);
      setRemoteBooks((current) => current.filter((book) => book.id !== bookId));
    },
    [accessToken, guestBooks, removeGuestBook]
  );

  return {
    books: [...guestBooks, ...remoteBooks],
    loading,
    error,
    reload: loadBooks,
    removeBook
  };
}
