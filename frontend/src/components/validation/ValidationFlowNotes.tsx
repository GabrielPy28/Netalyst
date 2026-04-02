import type { ProgramDetail } from "@/api/programs";
import { HiOutlineInformationCircle } from "react-icons/hi";
import { YOUTUBE_DAILY_UNITS_GUIDE, getYoutubeQuotaToday } from "@/lib/youtubeQuotaTracker";

function collectStepFunctions(program: ProgramDetail): Set<string> {
  const s = new Set<string>();
  for (const c of program.criteria) {
    for (const st of c.steps) {
      s.add(st.funcion_a_ejecutar.trim());
    }
  }
  return s;
}

type Props = {
  program: ProgramDetail;
  /** Unidades YouTube estimadas en la última corrida (tras completar validación). */
  lastYoutubeUnitsEstimate?: number;
};

export function ValidationFlowNotes({ program, lastYoutubeUnitsEstimate }: Props) {
  const fn = collectStepFunctions(program);
  const emailValidation =
    fn.has("hunter_verify_emails") || fn.has("screen_email_patterns");
  const apifyIg = fn.has("fetch_instagram_profiles");
  const apifyTt = fn.has("fetch_tiktok_profiles");
  const apifyFb = fn.has("fetch_facebook_recent_reel_activity");
  const youtube = fn.has("fetch_youtube_channels");
  const { units: ytToday } = getYoutubeQuotaToday();

  if (!emailValidation && !apifyIg && !apifyTt && !apifyFb && !youtube) {
    return null;
  }

  return (
    <div
      className="mt-6 space-y-4 rounded-xl border border-amber-400/35 bg-amber-950/40 px-4 py-4 text-base leading-relaxed text-slate-100"
      role="region"
      aria-label="Avisos sobre créditos y cuotas de API"
    >
      <div className="flex items-start gap-2 font-semibold text-amber-100">
        <HiOutlineInformationCircle className="mt-0.5 h-5 w-5 shrink-0 text-amber-300" />
        Antes de ejecutar la validación
      </div>
      <ul className="list-inside list-disc space-y-2 pl-1 text-slate-100 marker:text-amber-300">
        {emailValidation && (
          <li>
            <strong>Correos (Hunter / patrones):</strong> este flujo puede consumir créditos de
            verificación. Coordina con el líder de IT que existan créditos suficientes para el
            tamaño de tu lista antes de ejecutar.
          </li>
        )}
        {(apifyIg || apifyTt || apifyFb) && (
          <li>
            <strong>Redes sociales (Apify — Instagram, TikTok, Facebook):</strong> cada ejecución
            usa tu plan y límites de Apify. Revisa saldo y límites de rate en el panel de Apify; en
            listas grandes el tiempo y el consumo crecen.
          </li>
        )}
        {youtube && (
          <li>
            <strong>YouTube (Google Data API v3):</strong> el proyecto suele tener una cuota diaria
            del orden de <strong>{YOUTUBE_DAILY_UNITS_GUIDE.toLocaleString()} unidades</strong> por
            día (según configuración en Google Cloud). Este panel lleva un{" "}
            <strong>registro orientativo</strong> en tu navegador (no sustituye la consola de
            Google).
            {lastYoutubeUnitsEstimate != null && lastYoutubeUnitsEstimate > 0 ? (
              <>
                {" "}
                Última corrida (estimado): <strong>+{lastYoutubeUnitsEstimate}</strong> unidades.
              </>
            ) : null}{" "}
            Acumulado hoy en este navegador: <strong>{ytToday.toLocaleString()}</strong> unidades
            (estimado).
          </li>
        )}
      </ul>
    </div>
  );
}
