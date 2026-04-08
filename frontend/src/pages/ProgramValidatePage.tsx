import { motion } from "framer-motion";
import { FormEvent, useEffect, useRef, useState } from "react";
import { ValidationFlowNotes } from "@/components/validation/ValidationFlowNotes";
import { addYoutubeUnitsForSession } from "@/lib/youtubeQuotaTracker";
import {
  HiOutlineCheckCircle,
  HiOutlineClock,
  HiOutlineCloudUpload,
  HiOutlinePlay,
  HiOutlineXCircle,
} from "react-icons/hi";
import { Link, useParams } from "react-router-dom";
import Swal from "sweetalert2";
import type { ProgramDetail } from "@/api/programs";
import { fetchProgram } from "@/api/programs";
import type { ValidationStreamEvent, ValidationUploadResponse } from "@/api/validation";
import { uploadValidationStream, uploadValidationZip } from "@/api/validation";
import { PaginatedResultTable } from "@/components/validation/PaginatedResultTable";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { LOGO_URL } from "@/lib/constants";

function formatElapsed(ms: number): string {
  const s = Math.floor(ms / 1000);
  const m = Math.floor(s / 60);
  const rs = s % 60;
  if (m > 0) return `${m}m ${rs}s`;
  return `${rs}s`;
}

export function ProgramValidatePage() {
  const { id } = useParams<{ id: string }>();
  const [program, setProgram] = useState<ProgramDetail | null>(null);
  const [loadingProgram, setLoadingProgram] = useState(true);
  const [file, setFile] = useState<File | null>(null);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<ValidationUploadResponse | null>(null);
  const [youtubeLastEstimate, setYoutubeLastEstimate] = useState<number | undefined>();
  const [streamLog, setStreamLog] = useState<ValidationStreamEvent[]>([]);
  const [streamHeadline, setStreamHeadline] = useState("");
  const [elapsedMs, setElapsedMs] = useState(0);
  const [downloadingFullZip, setDownloadingFullZip] = useState(false);
  const streamLogRef = useRef<ValidationStreamEvent[]>([]);
  const validationAbortRef = useRef<AbortController | null>(null);
  const validationRunIdRef = useRef(0);

  useEffect(() => {
    return () => {
      validationAbortRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    if (!id) return;
    let c = false;
    (async () => {
      try {
        const p = await fetchProgram(id);
        if (!c) setProgram(p);
      } catch (e) {
        await Swal.fire({
          icon: "error",
          title: "No se pudo cargar el programa",
          text: e instanceof Error ? e.message : "Error",
          customClass: { popup: "netalyst-swal" },
        });
        if (!c) setProgram(null);
      } finally {
        if (!c) setLoadingProgram(false);
      }
    })();
    return () => {
      c = true;
    };
  }, [id]);

  useEffect(() => {
    if (!running) return;
    const t0 = Date.now();
    const id = window.setInterval(() => setElapsedMs(Date.now() - t0), 400);
    return () => window.clearInterval(id);
  }, [running]);

  function onFileChange(f: File | null) {
    setFile(f);
    setResult(null);
    setYoutubeLastEstimate(undefined);
    streamLogRef.current = [];
    setStreamLog([]);
    setStreamHeadline("");
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!id || !file) {
      await Swal.fire({
        icon: "warning",
        title: "Archivo requerido",
        text: "Selecciona un CSV o Excel (.csv, .xlsx, .xls).",
        customClass: { popup: "netalyst-swal" },
      });
      return;
    }
    streamLogRef.current = [];
    setStreamLog([]);
    setStreamHeadline("Iniciando…");
    setElapsedMs(0);
    validationAbortRef.current?.abort();
    const runId = ++validationRunIdRef.current;
    const ac = new AbortController();
    validationAbortRef.current = ac;
    setRunning(true);
    try {
      const data = await uploadValidationStream(
        id,
        file,
        (ev) => {
          streamLogRef.current = [...streamLogRef.current, ev].slice(-100);
          setStreamLog(streamLogRef.current);
          if (ev.type === "criterion_start") {
            setStreamHeadline(`Criterio ${ev.orden}: ${ev.criterion_nombre}`);
          }
          if (ev.type === "step_start") {
            setStreamHeadline(
              `${ev.criterion_nombre} — Paso ${ev.paso_num}: ${ev.step_nombre} (${ev.funcion_a_ejecutar})`,
            );
          }
        },
        { signal: ac.signal },
      );
      setResult(data);
      const merged = [...data.preview, ...data.excluded_preview];
      const ytAdd = addYoutubeUnitsForSession(merged);
      setYoutubeLastEstimate(ytAdd > 0 ? ytAdd : undefined);
      setStreamHeadline("Completado");
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        return;
      }
      if (err instanceof Error && err.name === "AbortError") {
        return;
      }
      const recent = streamLogRef.current.filter((e) => e.type === "step_done").slice(-8);
      const lines = recent
        .map((e) => {
          if (e.type !== "step_done") return "";
          const ok = e.ok ? "✓" : "✗";
          return `${ok} ${e.funcion_a_ejecutar}: ${e.step_nombre}`;
        })
        .filter(Boolean)
        .join("<br/>");
      await Swal.fire({
        icon: "error",
        title: "Validación fallida",
        html: `<p style="text-align:left">${err instanceof Error ? err.message : "Error"}</p>${lines ? `<p style="text-align:left;font-size:12px;margin-top:12px;opacity:.85"><strong>Últimos pasos:</strong><br/>${lines}</p>` : ""}`,
        customClass: { popup: "netalyst-swal" },
      });
    } finally {
      if (validationAbortRef.current === ac) {
        validationAbortRef.current = null;
      }
      if (runId === validationRunIdRef.current) {
        setRunning(false);
      }
    }
  }

  async function onDownloadFullZip() {
    if (!id || !file) return;
    setDownloadingFullZip(true);
    try {
      const blob = await uploadValidationZip(id, file);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "creadores_resultado.zip";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      await Swal.fire({
        icon: "error",
        title: "No se pudo descargar el ZIP completo",
        text: e instanceof Error ? e.message : "Error",
        customClass: { popup: "netalyst-swal" },
      });
    } finally {
      setDownloadingFullZip(false);
    }
  }

  if (loadingProgram) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-brand-dark text-lg text-slate-200">
        Cargando…
      </div>
    );
  }

  if (!program || !id) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-brand-dark">
        <p className="text-base text-slate-200">Programa no encontrado.</p>
        <Link to="/programas">
          <Button type="button">Volver a programas</Button>
        </Link>
      </div>
    );
  }

  const noCriteria = program.criteria.length === 0;

  return (
    <div className="min-h-screen bg-brand-dark text-brand-white">
      <header className="border-b border-white/10 bg-slate-900/50 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-4 md:px-8">
          <Link
            to={`/programas/${id}`}
            className="flex items-center gap-2 text-base text-slate-200 hover:text-brand-white"
          >
            <img src={LOGO_URL} alt="" className="h-8 w-auto opacity-80" />
            ← Volver al programa
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-10 md:px-8">
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
          <div className="mb-2 inline-flex items-center gap-2 text-brand-green">
            <HiOutlinePlay className="h-5 w-5" />
            <span className="text-base font-medium uppercase tracking-wide">Validación</span>
          </div>
          <h1 className="font-display text-3xl font-bold md:text-4xl">{program.nombre}</h1>
          <p className="mt-2 max-w-3xl text-base leading-relaxed text-slate-200">
            Sube la lista de creadores (CSV o Excel). Al terminar la validación verás todas las filas
            (válidas y excluidas) con paginación. Puedes elegir vista y descarga con{" "}
            <strong className="text-slate-100">columnas clave</strong> (operación diaria) o{" "}
            <strong className="text-slate-100">archivo completo</strong> con todas las columnas del
            pipeline — sin volver a ejecutar el flujo.
          </p>
        </motion.div>

        {noCriteria && (
          <div className="mt-6 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-base leading-relaxed text-amber-50">
            Este programa no tiene criterios configurados.{" "}
            <Link to={`/programas/${id}`} className="font-semibold underline hover:text-white">
              Define el flujo
            </Link>{" "}
            antes de validar, o la ejecución no aplicará pasos.
          </div>
        )}

        <ValidationFlowNotes program={program} lastYoutubeUnitsEstimate={youtubeLastEstimate} />

        <Card className="mt-8 border-brand-purple/25">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl">
              <HiOutlineCloudUpload className="h-6 w-6 text-brand-purple" />
              Archivo a validar
            </CardTitle>
            <p className="text-base leading-relaxed text-slate-200">
              Formatos: .csv, .xlsx, .xls. Las columnas deben ser las que espera el pipeline (p. ej.
              handles de redes según tu plantilla).
            </p>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="space-y-6">
              <div>
                <label className="mb-2 block text-sm font-medium uppercase tracking-wide text-slate-300">
                  Archivo
                </label>
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls,text/csv,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                  className="block w-full text-base text-slate-100 file:mr-4 file:rounded-lg file:border-0 file:bg-brand-purple/20 file:px-4 file:py-2 file:text-base file:font-semibold file:text-brand-purple hover:file:bg-brand-purple/30"
                  onChange={(e) => onFileChange(e.target.files?.[0] ?? null)}
                />
              </div>
              <div className="flex flex-wrap gap-3">
                <Button type="submit" disabled={running || !file} className="gap-2 text-base">
                  <HiOutlinePlay className="h-5 w-5" />
                  {running ? "Ejecutando…" : "Ejecutar validación"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {(running || streamLog.length > 0) && (
          <Card className="mt-6 border-white/15">
            <CardHeader>
              <CardTitle className="flex flex-wrap items-center gap-2 text-xl">
                <HiOutlineClock className="h-6 w-6 text-brand-yellow" />
                Progreso del flujo
              </CardTitle>
              <p className="text-base leading-relaxed text-slate-200">
                {running
                  ? "El servidor va enviando cada criterio y paso. Las llamadas a redes (Apify / YouTube API) pueden tardar varios segundos o minutos por lote."
                  : "Última ejecución (puedes volver a validar para limpiar esta vista)."}
              </p>
            </CardHeader>
            <CardContent className="space-y-4">
              {running && (
                <div className="flex flex-wrap items-center gap-3 text-base">
                  <span className="rounded-full bg-brand-purple/25 px-4 py-1.5 font-mono text-base text-brand-purple">
                    {formatElapsed(elapsedMs)}
                  </span>
                  <span className="font-medium text-slate-100">{streamHeadline}</span>
                </div>
              )}
              <div className="max-h-[min(480px,55vh)] overflow-y-auto rounded-lg border border-white/15 bg-slate-950/80 p-4 text-sm leading-relaxed text-slate-100">
                {streamLog.length === 0 && running && (
                  <p className="text-base text-slate-300">Esperando primer evento del servidor…</p>
                )}
                {streamLog.map((ev, idx) => {
                  if (ev.type === "criterion_start") {
                    return (
                      <div
                        key={idx}
                        className="mb-3 border-l-4 border-brand-pink/80 pl-3 text-base font-semibold text-pink-200"
                      >
                        ▸ Criterio {ev.orden}: {ev.criterion_nombre}
                      </div>
                    );
                  }
                  if (ev.type === "step_start") {
                    return (
                      <div key={idx} className="mb-2 pl-3 text-base text-slate-300">
                        Paso {ev.paso_num}: {ev.step_nombre}{" "}
                        <span className="text-slate-400">({ev.funcion_a_ejecutar})</span>
                      </div>
                    );
                  }
                  if (ev.type === "step_done") {
                    return (
                      <div
                        key={idx}
                        className={`mb-3 flex flex-wrap items-start gap-2 pl-3 text-base ${
                          ev.ok ? "text-emerald-200" : "text-red-300"
                        }`}
                      >
                        {ev.ok ? (
                          <HiOutlineCheckCircle className="mt-0.5 h-5 w-5 shrink-0 text-emerald-400" />
                        ) : (
                          <HiOutlineXCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-400" />
                        )}
                        <span>
                          <span className="font-medium">Listo paso {ev.paso_num}</span> —{" "}
                          {ev.funcion_a_ejecutar}
                          {ev.logs_tail?.length ? (
                            <span className="mt-2 block text-sm font-normal text-slate-300">
                              {ev.logs_tail.map((log, i) => (
                                <span key={i} className="mb-1 mr-2 inline-block">
                                  {String((log as { message?: string }).message ?? JSON.stringify(log))}
                                </span>
                              ))}
                            </span>
                          ) : null}
                        </span>
                      </div>
                    );
                  }
                  return null;
                })}
              </div>
            </CardContent>
          </Card>
        )}

        {result && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-10 space-y-6"
          >
            <Card>
              <CardHeader>
                <CardTitle className="text-xl">Resultado</CardTitle>
                <p className="text-base text-slate-200">
                  {result.program_nombre} · {result.rows} filas válidas · {result.excluded_rows}{" "}
                  excluidas
                </p>
                {(result.preview_truncated || result.excluded_preview_truncated) && (
                  <p className="mt-2 text-sm text-amber-300">
                    Vista parcial por volumen alto. Se muestran filas limitadas para evitar cortes de
                    red en archivos grandes.
                  </p>
                )}
                <div className="mt-4">
                  <Button
                    type="button"
                    variant="outline"
                    className="text-sm text-slate-100"
                    disabled={downloadingFullZip || !file}
                    onClick={onDownloadFullZip}
                  >
                    {downloadingFullZip
                      ? "Generando ZIP completo..."
                      : "Descargar ZIP completo (todos los registros)"}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <details className="rounded-lg border border-white/10 bg-slate-900/40 px-3 py-2 text-base text-slate-200">
                  <summary className="cursor-pointer font-medium text-slate-100">
                    Columnas completas del pipeline ({result.columns.length}) — tocar para expandir
                  </summary>
                  <p className="mt-3 text-sm leading-relaxed text-slate-300">
                    {result.columns.join(", ")}
                  </p>
                </details>
                <div className="mt-6 space-y-3">
                  <p className="text-base font-semibold text-slate-100">
                    Criterios ejecutados y registros
                  </p>
                  {result.criteria.map((c) => (
                    <details
                      key={c.criterion_id}
                      className="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2"
                    >
                      <summary className="cursor-pointer text-base text-slate-100">
                        <span className="text-brand-purple">Orden {c.orden}</span> — {c.criterion_nombre}{" "}
                        · {c.pasos_ejecutados.length} pasos · {c.logs.length} líneas de log
                      </summary>
                      <ul className="mt-2 space-y-2 border-t border-white/10 pt-3 text-sm text-slate-200">
                        {c.logs.length === 0 ? (
                          <li>Sin entradas de log en este criterio.</li>
                        ) : (
                          c.logs.map((log, i) => {
                            const fn = String((log as { funcion?: string }).funcion ?? "");
                            const msg = String((log as { message?: string }).message ?? "");
                            const ok = (log as { ok?: boolean }).ok;
                            return (
                              <li
                                key={i}
                                className={ok === false ? "text-red-400" : ok === true ? "text-brand-green/90" : ""}
                              >
                                {fn && <span className="text-brand-purple">{fn}</span>}
                                {fn && msg ? " · " : ""}
                                {msg || JSON.stringify(log)}
                              </li>
                            );
                          })
                        )}
                      </ul>
                    </details>
                  ))}
                </div>
                <PaginatedResultTable
                  rows={result.preview}
                  columnOrder={result.columns}
                  title="Creadores válidos"
                  exportBasename="creadores_validos"
                />
                <PaginatedResultTable
                  rows={result.excluded_preview}
                  columnOrder={
                    result.excluded_preview.length > 0
                      ? Object.keys(result.excluded_preview[0] ?? {})
                      : result.columns
                  }
                  title="Creadores excluidos"
                  exportBasename="creadores_excluidos"
                  emptyMessage="No hay filas excluidas en esta ejecución."
                  isExcludedTable
                />
              </CardContent>
            </Card>
          </motion.div>
        )}
      </main>
    </div>
  );
}
