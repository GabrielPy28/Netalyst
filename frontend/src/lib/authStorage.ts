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

function base64UrlDecode(input: string): string {
  const b64 = input.replace(/-/g, "+").replace(/_/g, "/");
  const padded = b64.padEnd(Math.ceil(b64.length / 4) * 4, "=");
  return atob(padded);
}

export function isTokenValid(token: string | null): boolean {
  if (!token) return false;
  const parts = token.split(".");
  if (parts.length !== 3) return false;
  try {
    const payload = JSON.parse(base64UrlDecode(parts[1])) as { exp?: number };
    if (typeof payload.exp !== "number") return false;
    const nowSec = Math.floor(Date.now() / 1000);
    return payload.exp > nowSec;
  } catch {
    return false;
  }
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
