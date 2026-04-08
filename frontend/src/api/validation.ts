import { apiBase } from "./client";
import { getToken } from "@/lib/authStorage";

function errorFromBody(data: Record<string, unknown>): string {
  const d = data.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d))
    return d.map((x: { msg?: string }) => x.msg ?? JSON.stringify(x)).join(", ");
  return "Error en la solicitud";
}

export type PasoEjecutadoOut = {
  paso_num: number;
  nombre: string;
  funcion_a_ejecutar: string;
};

export type CriterionRunOut = {
  criterion_id: string;
  criterion_nombre: string;
  objetivo: string | null;
  orden: number;
  pasos_ejecutados: PasoEjecutadoOut[];
  logs: Record<string, unknown>[];
};

export type ValidationUploadResponse = {
  program_id: string;
  program_nombre: string;
  rows: number;
  excluded_rows: number;
  columns: string[];
  criteria: CriterionRunOut[];
  /** Todas las filas válidas (mismo contenido que creadores_validos en Excel). */
  preview: Record<string, unknown>[];
  /** Todas las filas excluidas. */
  excluded_preview: Record<string, unknown>[];
  /** True cuando el backend limita el preview por volumen. */
  preview_truncated?: boolean;
  /** True cuando el backend limita el preview excluido por volumen. */
  excluded_preview_truncated?: boolean;
};

export type ValidationStreamEvent =
  | { type: "criterion_start"; criterion_id: string; criterion_nombre: string; orden: number }
  | {
      type: "step_start";
      criterion_nombre: string;
      criterion_orden: number;
      paso_num: number;
      step_nombre: string;
      funcion_a_ejecutar: string;
    }
  | {
      type: "step_done";
      criterion_nombre: string;
      criterion_orden: number;
      paso_num: number;
      step_nombre: string;
      funcion_a_ejecutar: string;
      ok: boolean;
      logs_tail: Record<string, unknown>[];
    }
  | ({ type: "complete" } & ValidationUploadResponse)
  | { type: "error"; message: string };

type ValidationJobStatusResponse = {
  job_id: string;
  status: "running" | "complete" | "error";
  response_mode: "json" | "zip";
  events_tail: Record<string, unknown>[];
  result?: ValidationUploadResponse;
  summary?: { program_nombre: string; rows: number; excluded_rows: number };
  download_ready?: boolean;
  error_message?: string | null;
};

function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const id = window.setTimeout(() => resolve(), ms);
    const onAbort = () => {
      window.clearTimeout(id);
      reject(new DOMException("Aborted", "AbortError"));
    };
    if (signal?.aborted) {
      onAbort();
      return;
    }
    signal?.addEventListener("abort", onAbort, { once: true });
  });
}

export type UploadValidationStreamOptions = {
  /** Si se aborta (p. ej. al salir de la página), deja de hacer polling. */
  signal?: AbortSignal;
  /**
   * Snapshot del tail de eventos del servidor (cada poll). Sustituye al stream SSE
   * para corridas de muchas horas sin una sola conexión HTTP larga.
   */
  onTail?: (events: ValidationStreamEvent[]) => void;
};

/**
 * Encola validación y hace polling hasta obtener el resultado JSON.
 * Adecuado para listas enormes o pasos lentos (horas); evita timeouts de proxy/CDN.
 */
export async function uploadValidationStream(
  programId: string,
  file: File,
  options?: UploadValidationStreamOptions,
): Promise<ValidationUploadResponse> {
  const token = getToken();
  if (!token) throw new Error("Sesión requerida");
  const fd = new FormData();
  fd.append("program_id", programId);
  fd.append("file", file);
  fd.append("response_mode", "json");

  const res = await fetch(`${apiBase}/validation/jobs`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: fd,
    signal: options?.signal,
  });

  if (res.status !== 202) {
    const data = (await res.json().catch(() => ({}))) as Record<string, unknown>;
    throw new Error(errorFromBody(data) || res.statusText);
  }

  const created = (await res.json()) as { job_id: string; poll_interval_seconds?: number };
  const intervalMs = Math.max(1000, (created.poll_interval_seconds ?? 2.5) * 1000);
  const jobId = created.job_id;

  let first = true;
  while (true) {
    if (!first) {
      if (options?.signal?.aborted) {
        throw new DOMException("Aborted", "AbortError");
      }
      await sleep(intervalMs, options?.signal);
    }
    first = false;

    const stRes = await fetch(`${apiBase}/validation/jobs/${jobId}`, {
      headers: { Authorization: `Bearer ${token}` },
      signal: options?.signal,
    });
    const st = (await stRes.json().catch(() => ({}))) as ValidationJobStatusResponse & Record<string, unknown>;
    if (!stRes.ok) {
      throw new Error(errorFromBody(st) || stRes.statusText);
    }

    if (options?.onTail && Array.isArray(st.events_tail)) {
      options.onTail(st.events_tail as ValidationStreamEvent[]);
    }

    if (st.status === "error") {
      throw new Error(st.error_message || "Error en validación");
    }
    if (st.status === "complete" && st.result) {
      return st.result;
    }
  }
}

export async function uploadValidationJson(
  programId: string,
  file: File,
): Promise<ValidationUploadResponse> {
  const token = getToken();
  if (!token) throw new Error("Sesión requerida");
  const fd = new FormData();
  fd.append("program_id", programId);
  fd.append("file", file);
  fd.append("response_mode", "json");
  const res = await fetch(`${apiBase}/validation/upload`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: fd,
  });
  const data = (await res.json().catch(() => ({}))) as Record<string, unknown>;
  if (!res.ok) {
    throw new Error(errorFromBody(data) || res.statusText);
  }
  return data as unknown as ValidationUploadResponse;
}

export type UploadValidationZipOptions = {
  signal?: AbortSignal;
};

export async function uploadValidationZip(
  programId: string,
  file: File,
  options?: UploadValidationZipOptions,
): Promise<Blob> {
  const token = getToken();
  if (!token) throw new Error("Sesión requerida");
  const fd = new FormData();
  fd.append("program_id", programId);
  fd.append("file", file);
  fd.append("response_mode", "zip");

  const res = await fetch(`${apiBase}/validation/jobs`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: fd,
    signal: options?.signal,
  });

  if (res.status !== 202) {
    const data = (await res.json().catch(() => ({}))) as Record<string, unknown>;
    throw new Error(errorFromBody(data) || res.statusText);
  }

  const created = (await res.json()) as { job_id: string; poll_interval_seconds?: number };
  const intervalMs = Math.max(1000, (created.poll_interval_seconds ?? 2.5) * 1000);
  const jobId = created.job_id;

  let first = true;
  while (true) {
    if (!first) {
      if (options?.signal?.aborted) {
        throw new DOMException("Aborted", "AbortError");
      }
      await sleep(intervalMs, options?.signal);
    }
    first = false;

    const stRes = await fetch(`${apiBase}/validation/jobs/${jobId}`, {
      headers: { Authorization: `Bearer ${token}` },
      signal: options?.signal,
    });
    const st = (await stRes.json().catch(() => ({}))) as ValidationJobStatusResponse & Record<string, unknown>;
    if (!stRes.ok) {
      throw new Error(errorFromBody(st) || stRes.statusText);
    }

    if (st.status === "error") {
      throw new Error(st.error_message || "Error generando ZIP");
    }
    if (st.status === "complete" && st.download_ready) {
      break;
    }
  }

  const dl = await fetch(`${apiBase}/validation/jobs/${jobId}/download`, {
    headers: { Authorization: `Bearer ${token}` },
    signal: options?.signal,
  });
  if (!dl.ok) {
    const data = (await dl.json().catch(() => ({}))) as Record<string, unknown>;
    throw new Error(errorFromBody(data) || dl.statusText);
  }
  return dl.blob();
}
