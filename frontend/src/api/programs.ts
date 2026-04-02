import { apiDeleteAuth, apiGetAuth, apiPostAuth, apiPutAuth } from "./client";

export type CatalogStep = {
  paso_num: number;
  nombre: string;
  definicion: string;
  funcion_a_ejecutar: string;
};

export type CriterionCatalogItem = {
  slug: string;
  nombre: string;
  objetivo: string;
  entrega_usuario: string;
  salida_esperada: string;
  steps: CatalogStep[];
};

export type ProgramListItem = {
  id: string;
  nombre: string;
  brand: string | null;
  image_brand_url: string | null;
  descripcion: string | null;
  is_active: boolean;
  criterios_count: number;
};

export type CriterionStepOut = {
  id: string;
  paso_num: number;
  nombre: string;
  definicion: string | null;
  funcion_a_ejecutar: string;
};

export type CriterionOut = {
  id: string;
  nombre: string;
  objetivo: string | null;
  template_slug: string | null;
  orden: number;
  steps: CriterionStepOut[];
};

export type ProgramDetail = {
  id: string;
  nombre: string;
  brand: string | null;
  image_brand_url: string | null;
  descripcion: string | null;
  is_active: boolean;
  criteria: CriterionOut[];
};

export type ProgramCreateFromFlow = {
  nombre: string;
  descripcion?: string | null;
  brand?: string | null;
  image_brand_url?: string | null;
  is_active?: boolean;
  criterio_slugs: string[];
};

export type ProgramReplaceFlow = {
  criterio_slugs: string[];
};

export function fetchCriterionCatalog() {
  return apiGetAuth<CriterionCatalogItem[]>("/programs/criterion-catalog");
}

export function fetchPrograms() {
  return apiGetAuth<ProgramListItem[]>("/programs");
}

export function fetchProgram(id: string) {
  return apiGetAuth<ProgramDetail>(`/programs/${id}`);
}

export function createProgramFromFlow(payload: ProgramCreateFromFlow) {
  return apiPostAuth<ProgramCreateFromFlow, ProgramDetail>("/programs/from-flow", payload);
}

export function replaceProgramFlow(programId: string, payload: ProgramReplaceFlow) {
  return apiPutAuth<ProgramReplaceFlow, ProgramDetail>(`/programs/${programId}/flow`, payload);
}

export function deleteProgram(programId: string) {
  return apiDeleteAuth(`/programs/${programId}`);
}
