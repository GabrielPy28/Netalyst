import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { LoginPage } from "@/pages/LoginPage";
import { ProgramDetailPage } from "@/pages/ProgramDetailPage";
import { ProgramNewPage } from "@/pages/ProgramNewPage";
import { ProgramsPage } from "@/pages/ProgramsPage";
import { ProgramValidatePage } from "@/pages/ProgramValidatePage";
import { WelcomePage } from "@/pages/WelcomePage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/welcome"
          element={
            <ProtectedRoute>
              <WelcomePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/programas"
          element={
            <ProtectedRoute>
              <ProgramsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/programas/nuevo"
          element={
            <ProtectedRoute>
              <ProgramNewPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/programas/:id/validar"
          element={
            <ProtectedRoute>
              <ProgramValidatePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/programas/:id"
          element={
            <ProtectedRoute>
              <ProgramDetailPage />
            </ProtectedRoute>
          }
        />
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
