import * as XLSX from "xlsx";

/** Aplana valores para celdas Excel (evita objetos crudos). */
function cellValue(v: unknown): string | number | boolean {
  if (v === null || v === undefined) return "";
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "boolean") return v;
  if (typeof v === "string") return v;
  try {
    return JSON.stringify(v);
  } catch {
    return String(v);
  }
}

function orderRows(
  rows: Record<string, unknown>[],
  columnOrder: string[] | undefined,
): Record<string, unknown>[] {
  if (!columnOrder?.length) return rows;
  return rows.map((r) => {
    const o: Record<string, unknown> = {};
    for (const c of columnOrder) {
      o[c] = r[c] ?? "";
    }
    return o;
  });
}

/**
 * Descarga un .xlsx desde filas ya cargadas (sin volver a llamar al API).
 */
export function downloadRowsAsXlsx(
  rows: Record<string, unknown>[],
  filename: string,
  columnOrder?: string[],
): void {
  const ordered = orderRows(rows, columnOrder).map((r) => {
    const flat: Record<string, string | number | boolean> = {};
    for (const [k, v] of Object.entries(r)) {
      flat[k] = cellValue(v);
    }
    return flat;
  });

  const ws =
    ordered.length === 0
      ? XLSX.utils.aoa_to_sheet([["Sin filas en esta tabla"]])
      : XLSX.utils.json_to_sheet(ordered);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Datos");
  XLSX.writeFile(wb, filename.endsWith(".xlsx") ? filename : `${filename}.xlsx`);
}
