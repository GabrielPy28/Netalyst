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

function validationResponseFromComplete(ev: ValidationStreamEvent): ValidationUploadResponse {
  const e = ev as Record<string, unknown>;
  const { type: _t, ...rest } = e;
  return rest as unknown as ValidationUploadResponse;
}

export type UploadValidationStreamOptions = {
  /** Si se aborta (p. ej. al salir de la página), el servidor puede cortar el pipeline y liberar el worker. */
  signal?: AbortSignal;
};

export async function uploadValidationStream(
  programId: string,
  file: File,
  onEvent: (ev: ValidationStreamEvent) => void,
  options?: UploadValidationStreamOptions,
): Promise<ValidationUploadResponse> {
  const token = getToken();
  if (!token) throw new Error("Sesión requerida");
  const fd = new FormData();
  fd.append("program_id", programId);
  fd.append("file", file);
  fd.append("response_mode", "json");

  const res = await fetch(`${apiBase}/validation/upload-stream`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: fd,
    signal: options?.signal,
  });

  if (!res.ok) {
    const data = (await res.json().catch(() => ({}))) as Record<string, unknown>;
    throw new Error(errorFromBody(data) || res.statusText);
  }

  const reader = res.body?.getReader();
  if (!reader) {
    throw new Error("El navegador no soporta lectura del stream de progreso.");
  }

  const dec = new TextDecoder();
  let buf = "";
  let complete: ValidationUploadResponse | null = null;

  try {
    outer: while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const chunks = buf.split("\n\n");
      buf = chunks.pop() ?? "";
      for (const rawBlock of chunks) {
        const block = rawBlock.trim();
        if (!block) continue;
        for (const line of block.split("\n")) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data:")) continue;
          const json = trimmed.slice(5).trim();
          if (!json) continue;
          let ev: ValidationStreamEvent;
          try {
            ev = JSON.parse(json) as ValidationStreamEvent;
          } catch {
            continue;
          }
          onEvent(ev);
          if (ev.type === "complete") {
            complete = validationResponseFromComplete(ev);
            break outer;
          }
          if (ev.type === "error") {
            throw new Error(ev.message);
          }
        }
      }
    }
  } finally {
    await reader.cancel().catch(() => {});
    try {
      reader.releaseLock();
    } catch {
      /* ya liberado */
    }
  }

  if (!complete) {
    throw new Error("La validación terminó sin recibir el resultado final. Revisa la consola del API.");
  }
  return complete;
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

export async function uploadValidationZip(programId: string, file: File): Promise<Blob> {
  const token = getToken();
  if (!token) throw new Error("Sesión requerida");
  const fd = new FormData();
  fd.append("program_id", programId);
  fd.append("file", file);
  fd.append("response_mode", "zip");
  const res = await fetch(`${apiBase}/validation/upload`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: fd,
  });
  if (!res.ok) {
    const data = (await res.json().catch(() => ({}))) as Record<string, unknown>;
    throw new Error(errorFromBody(data) || res.statusText);
  }
  return res.blob();
}
