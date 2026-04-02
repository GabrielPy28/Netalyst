import { getToken } from "@/lib/authStorage";

export const apiBase = import.meta.env.VITE_API_BASE ?? "/api/v1";

function formatErrorDetail(data: Record<string, unknown>): string {
  const d = data.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d))
    return d.map((x: { msg?: string }) => x.msg ?? JSON.stringify(x)).join(", ");
  return "Error en la solicitud";
}

export async function apiPost<TBody, TRes>(
  path: string,
  body: TBody,
  extraHeaders?: HeadersInit,
): Promise<TRes> {
  const res = await fetch(`${apiBase}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...extraHeaders },
    body: JSON.stringify(body),
  });
  const data = (await res.json().catch(() => ({}))) as Record<string, unknown>;
  if (!res.ok) {
    throw new Error(formatErrorDetail(data) || res.statusText);
  }
  return data as TRes;
}

export async function apiGetAuth<T>(path: string): Promise<T> {
  const token = getToken();
  if (!token) throw new Error("Sesión requerida");
  const res = await fetch(`${apiBase}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = (await res.json().catch(() => ({}))) as Record<string, unknown>;
  if (!res.ok) {
    throw new Error(formatErrorDetail(data) || res.statusText);
  }
  return data as T;
}

export async function apiPostAuth<TBody, TRes>(path: string, body: TBody): Promise<TRes> {
  const token = getToken();
  if (!token) throw new Error("Sesión requerida");
  return apiPost<TBody, TRes>(path, body, { Authorization: `Bearer ${token}` });
}

export async function apiPutAuth<TBody, TRes>(path: string, body: TBody): Promise<TRes> {
  const token = getToken();
  if (!token) throw new Error("Sesión requerida");
  const res = await fetch(`${apiBase}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  const data = (await res.json().catch(() => ({}))) as Record<string, unknown>;
  if (!res.ok) {
    throw new Error(formatErrorDetail(data) || res.statusText);
  }
  return data as TRes;
}

export async function apiDeleteAuth(path: string): Promise<void> {
  const token = getToken();
  if (!token) throw new Error("Sesión requerida");
  const res = await fetch(`${apiBase}${path}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const data = (await res.json().catch(() => ({}))) as Record<string, unknown>;
    throw new Error(formatErrorDetail(data) || res.statusText);
  }
}
