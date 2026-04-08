import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { clearSession, getToken, isTokenValid } from "@/lib/authStorage";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const location = useLocation();
  const token = getToken();
  if (!isTokenValid(token)) {
    clearSession();
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  return <>{children}</>;
}
