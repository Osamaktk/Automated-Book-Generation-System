import { useCallback, useState } from "react";

import { useGuestSession } from "../context/GuestStorageContext";
import { useAuth } from "./useAuth";
import { createBook } from "../services/bookService";

export function useSyncOnLogin() {
  const { accessToken, isAuthenticated } = useAuth();
  const { getBookDetail, guestBooks, deleteGuestBook } = useGuestSession();
  const [syncing, setSyncing] = useState(false);

  const syncGuestBook = useCallback(
    async (bookId) => {
      if (!isAuthenticated || !accessToken) {
        throw new Error("Authentication is required to sync guest data.");
      }

      const detail = getBookDetail(bookId);
      if (!detail?.book) {
        throw new Error("Guest book not found.");
      }

      setSyncing(true);
      try {
        const response = await createBook(
          {
            title: detail.book.title,
            notes: detail.book.notes
          },
          accessToken
        );

        const remoteBookId = response?.book?.id || response?.book_id;
        deleteGuestBook(bookId);

        return {
          remoteBookId,
          warning:
            "Guest chapters and local outline revisions were not uploaded because the backend does not yet expose direct import endpoints."
        };
      } finally {
        setSyncing(false);
      }
    },
    [accessToken, deleteGuestBook, getBookDetail, isAuthenticated]
  );

  const syncAllGuestBooks = useCallback(async () => {
    const results = [];
    for (const book of guestBooks) {
      results.push(await syncGuestBook(book.id));
    }
    return results;
  }, [guestBooks, syncGuestBook]);

  return {
    syncing,
    syncGuestBook,
    syncAllGuestBooks
  };
}
