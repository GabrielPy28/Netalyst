import { useEffect, useMemo, useState } from "react";
import {
  HiOutlineChevronLeft,
  HiOutlineChevronRight,
  HiOutlineDocumentDownload,
  HiOutlineTable,
} from "react-icons/hi";
import { Button } from "@/components/ui/Button";
import { slimColumnOrderForRows } from "@/lib/creatorSlimColumns";
import { downloadRowsAsXlsx } from "@/lib/exportXlsx";

const DEFAULT_PAGE_SIZE = 15;

type PaginatedResultTableProps = {
  rows: Record<string, unknown>[];
  title: string;
  /** Orden de columnas completo (API). */
  columnOrder?: string[];
  /** Sin extensión: p. ej. creadores_validos → creadores_validos_columnas_clave.xlsx */
  exportBasename: string;
  emptyMessage?: string;
  /** Si la tabla es de excluidos, el export clave incluye exclusion_stage / exclusion_reason. */
  isExcludedTable?: boolean;
};

export function PaginatedResultTable({
  rows,
  title,
  columnOrder,
  exportBasename,
  emptyMessage = "No hay filas.",
  isExcludedTable = false,
}: PaginatedResultTableProps) {
  const [page, setPage] = useState(0);
  const [viewMode, setViewMode] = useState<"slim" | "full">("slim");
  const pageSize = DEFAULT_PAGE_SIZE;

  useEffect(() => {
    setPage(0);
  }, [rows.length, exportBasename]);

  const slimKeys = useMemo(
    () => slimColumnOrderForRows(rows, { isExcluded: isExcludedTable }),
    [rows, isExcludedTable],
  );

  const fullKeys = useMemo(() => {
    if (columnOrder?.length) return columnOrder;
    if (rows.length === 0) return [];
    return Object.keys(rows[0] ?? {});
  }, [rows, columnOrder]);

  const slimKeysEffective = slimKeys.length > 0 ? slimKeys : fullKeys;
  const keys = viewMode === "slim" ? slimKeysEffective : fullKeys;

  const totalPages = Math.max(1, Math.ceil(rows.length / pageSize) || 1);
  const safePage = Math.min(page, totalPages - 1);
  const start = safePage * pageSize;
  const pageRows = rows.slice(start, start + pageSize);

  if (rows.length === 0) {
    return (
      <div className="mt-6 rounded-lg border border-white/10 bg-white/[0.02] px-4 py-6">
        <p className="text-base font-medium text-slate-100">{title}</p>
        <p className="mt-2 text-base text-slate-300">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="mt-6 space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
        <p className="text-base font-semibold text-slate-100">{title}</p>
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-slate-300">
            {rows.length} fila{rows.length === 1 ? "" : "s"} · mostrando {keys.length} columnas
          </span>
        </div>
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:flex-wrap lg:items-center lg:justify-between">
        <div
          className="inline-flex rounded-lg border border-white/15 bg-slate-900/60 p-1"
          role="group"
          aria-label="Modo de columnas en pantalla"
        >
          <button
            type="button"
            onClick={() => setViewMode("slim")}
            className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
              viewMode === "slim"
                ? "bg-brand-purple/40 text-white"
                : "text-slate-300 hover:bg-white/5 hover:text-white"
            }`}
          >
            <HiOutlineTable className="h-4 w-4" />
            Columnas clave ({slimKeysEffective.length})
          </button>
          <button
            type="button"
            onClick={() => setViewMode("full")}
            className={`rounded-md px-3 py-2 text-sm font-medium transition-colors ${
              viewMode === "full"
                ? "bg-brand-purple/40 text-white"
                : "text-slate-300 hover:bg-white/5 hover:text-white"
            }`}
          >
            Todas ({fullKeys.length})
          </button>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            className="gap-2 border-emerald-500/40 text-sm text-emerald-100 hover:bg-emerald-950/50"
            onClick={() =>
              downloadRowsAsXlsx(
                rows,
                `${exportBasename}_columnas_clave.xlsx`,
                slimKeysEffective,
              )
            }
          >
            <HiOutlineDocumentDownload className="h-4 w-4" />
            Excel — columnas clave
          </Button>
          <Button
            type="button"
            variant="outline"
            className="gap-2 text-sm text-slate-100"
            onClick={() => downloadRowsAsXlsx(rows, `${exportBasename}_completo.xlsx`, fullKeys)}
          >
            <HiOutlineDocumentDownload className="h-4 w-4" />
            Excel — completo
          </Button>
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg border border-white/15">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="sticky top-0 z-[1] bg-slate-800 text-slate-200">
            <tr>
              {keys.map((k) => (
                <th key={k} className="whitespace-nowrap px-3 py-2.5 text-sm font-semibold">
                  {k}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, i) => (
              <tr key={start + i} className="border-t border-white/10 odd:bg-white/[0.04]">
                {keys.map((k) => (
                  <td
                    key={k}
                    className="max-w-[260px] truncate px-3 py-2 text-sm text-slate-100"
                    title={row[k] === null || row[k] === undefined ? "" : String(row[k])}
                  >
                    {row[k] === null || row[k] === undefined ? "—" : String(row[k])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-slate-200">
          <span>
            Filas {start + 1}–{Math.min(start + pageSize, rows.length)} de {rows.length}
          </span>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              className="h-9 min-w-[2.25rem] px-2"
              disabled={safePage <= 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
            >
              <HiOutlineChevronLeft className="h-5 w-5" />
            </Button>
            <span className="tabular-nums text-slate-100">
              Página {safePage + 1} / {totalPages}
            </span>
            <Button
              type="button"
              variant="outline"
              className="h-9 min-w-[2.25rem] px-2"
              disabled={safePage >= totalPages - 1}
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            >
              <HiOutlineChevronRight className="h-5 w-5" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
