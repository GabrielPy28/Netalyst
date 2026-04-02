const STORAGE_KEY = "netalyst_youtube_quota_v1";

type QuotaStore = {
  day: string;
  /** Unidades aproximadas (no es la cuota exacta de Google; orientativa). */
  units: number;
};

function todayUtc(): string {
  return new Date().toISOString().slice(0, 10);
}

function readStore(): QuotaStore {
  const d = todayUtc();
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { day: d, units: 0 };
    const p = JSON.parse(raw) as QuotaStore;
    if (p.day !== d) return { day: d, units: 0 };
    return { day: p.day, units: Number(p.units) || 0 };
  } catch {
    return { day: d, units: 0 };
  }
}

/** Google suele publicar ~10.000 unidades/día para la Data API v3 (según proyecto). */
export const YOUTUBE_DAILY_UNITS_GUIDE = 10_000;

/**
 * Heurística: por fila con consulta YouTube aparentemente exitosa, ~3 unidades
 * (canal + lista uploads + último video). Ajustable sin backend.
 */
export function estimateYoutubeApiUnits(rows: Record<string, unknown>[]): number {
  let n = 0;
  for (const r of rows) {
    const src = String(r.yt_fetch_source ?? "").trim();
    const err = String(r.yt_fetch_error ?? "").trim();
    if (!src || src === "skipped") continue;
    if (err) continue;
    n += 1;
  }
  return n * 3;
}

export function addYoutubeUnitsForSession(rows: Record<string, unknown>[]): number {
  const add = estimateYoutubeApiUnits(rows);
  if (add <= 0) return 0;
  const s = readStore();
  s.units += add;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
  return add;
}

export function getYoutubeQuotaToday(): { units: number; day: string } {
  const s = readStore();
  return { units: s.units, day: s.day };
}
