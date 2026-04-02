/**
 * Columnas del archivo estándar de creadores (operación diaria).
 * Debe coincidir con backend `app.constants.creator_file_columns.CREATOR_FILE_COLUMNS`.
 */
export const CREATOR_SLIM_COLUMNS: readonly string[] = [
  "email",
  "first_name",
  "last_name",
  "full_name",
  "picture",
  "username",
  "instagram_url",
  "tiktok_url",
  "youtube_channel_url",
  "instagram_username",
  "tiktok_username",
  "youtube_channel",
  "category",
  "facebook_page",
  "personalized_paragraph",
  "max_followers",
  "main_platform",
  "status",
  "instagram_followers",
  "instagram_post_count",
  "instagram_picture",
  "instagram_bio",
  "instagram_category",
  "instagram_verified",
  "tiktok_followers",
  "tiktok_post_count",
  "tiktok_picture",
  "tiktok_bio",
  "tiktok_category",
  "tiktok_verified",
  "youtube_followers",
  "youtube_post_count",
  "youtube_picture",
  "youtube_bio",
  "youtube_category",
  "youtube_verified",
] as const;

export function slimColumnOrderForRow(row: Record<string, unknown>): string[] {
  return CREATOR_SLIM_COLUMNS.filter((c) => c in row);
}

/** Columnas clave presentes en el dataset; en excluidos añade etapa/motivo si existen. */
export function slimColumnOrderForRows(
  rows: Record<string, unknown>[],
  options?: { isExcluded?: boolean },
): string[] {
  if (rows.length === 0) return [...CREATOR_SLIM_COLUMNS];
  const r = rows[0];
  const cols = CREATOR_SLIM_COLUMNS.filter((c) => c in r);
  if (options?.isExcluded) {
    for (const x of ["exclusion_stage", "exclusion_reason"] as const) {
      if (x in r && !cols.includes(x)) cols.push(x);
    }
  }
  return cols;
}
