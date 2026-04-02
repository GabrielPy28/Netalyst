import { STORAGE_TOKEN_KEY, STORAGE_USER_KEY } from "./constants";

export type StoredUser = {
  id: string;
  email: string;
  name: string;
  avatar_url: string;
};

export function getToken(): string | null {
  return localStorage.getItem(STORAGE_TOKEN_KEY);
}

export function getUser(): StoredUser | null {
  const raw = localStorage.getItem(STORAGE_USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StoredUser;
  } catch {
    return null;
  }
}

export function setSession(token: string, user: StoredUser) {
  localStorage.setItem(STORAGE_TOKEN_KEY, token);
  localStorage.setItem(STORAGE_USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(STORAGE_TOKEN_KEY);
  localStorage.removeItem(STORAGE_USER_KEY);
}
