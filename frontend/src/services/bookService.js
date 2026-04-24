import { downloadRequest, request, sharedRequest, streamRequest } from "./apiClient";

export async function getBooks(accessToken) {
  return request("/books", { accessToken });
}

export async function deleteBook(bookId, accessToken) {
  return request(`/books/${bookId}`, { method: "DELETE", accessToken });
}

export async function getBook(bookId, accessToken) {
  return request(`/books/${bookId}`, { accessToken });
}

export async function getSharedBook(bookId, shareToken) {
  return sharedRequest(`/books/${bookId}`, shareToken);
}

export async function getBookChapters(bookId, accessToken) {
  return request(`/books/${bookId}/chapters`, { accessToken });
}

export async function getSharedBookChapters(bookId, shareToken) {
  return sharedRequest(`/books/${bookId}/chapters`, shareToken);
}

export async function getChapter(chapterId, accessToken) {
  return request(`/chapters/${chapterId}`, { accessToken });
}

export async function submitOutlineFeedback(bookId, payload, accessToken) {
  return request(`/books/${bookId}/feedback`, {
    method: "POST",
    accessToken,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

export async function submitChapterFeedback(chapterId, payload, accessToken) {
  return request(`/chapters/${chapterId}/feedback`, {
    method: "POST",
    accessToken,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

export async function createBookStream(payload, accessToken, onEvent) {
  const response = await streamRequest("/books/create-stream", {
    accessToken,
    body: payload
  });
  await consumeEventStream(response, onEvent);
}

export async function generateChapterStream(bookId, accessToken, onEvent) {
  const response = await streamRequest(`/books/${bookId}/generate-chapter-stream`, {
    accessToken
  });
  await consumeEventStream(response, onEvent);
}

async function consumeEventStream(response, onEvent) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) {
        continue;
      }

      try {
        const event = JSON.parse(line.slice(6));
        onEvent?.(event);
      } catch {
        // Ignore malformed SSE chunks.
      }
    }
  }
}

export async function downloadCompiledBook(bookId, format, accessToken) {
  return downloadRequest(`/books/${bookId}/compile?format=${encodeURIComponent(format)}`, {
    accessToken
  });
}

export async function shareBookWithUser(bookId, sharedWith, accessToken) {
  return request(`/books/${bookId}/share/user`, {
    method: "POST",
    accessToken,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ shared_with: sharedWith })
  });
}

export async function createShareLink(bookId, accessToken) {
  return request(`/books/${bookId}/share/link`, {
    method: "POST",
    accessToken,
    headers: { "Content-Type": "application/json" }
  });
}
