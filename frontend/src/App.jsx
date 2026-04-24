import { Navigate, Route, Routes } from "react-router-dom";

import AuthModal from "./components/auth/AuthModal";
import AppShell from "./components/layout/AppShell";
import BookDetailPage from "./pages/BookDetailPage";
import ChapterDetailPage from "./pages/ChapterDetailPage";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import SharedBookPage from "./pages/SharedBookPage";

function App() {
  return (
    <>
      <AuthModal />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/shared" element={<SharedBookPage />} />
        <Route element={<AppShell />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/books/:bookId" element={<BookDetailPage />} />
          <Route path="/books/:bookId/chapters/:chapterId" element={<ChapterDetailPage />} />
        </Route>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </>
  );
}

export default App;
