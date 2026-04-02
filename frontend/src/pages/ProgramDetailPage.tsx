import { Reorder, motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import {
  HiOutlineClipboardList,
  HiOutlineDownload,
  HiOutlinePencil,
  HiOutlinePlay,
  HiOutlinePlus,
  HiOutlineTrash,
} from "react-icons/hi";
import { Link, useNavigate, useParams } from "react-router-dom";
import Swal from "sweetalert2";
import type { CriterionCatalogItem, ProgramDetail } from "@/api/programs";
import { deleteProgram, fetchCriterionCatalog, fetchProgram, replaceProgramFlow } from "@/api/programs";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { LOGO_URL } from "@/lib/constants";

const DEFAULT_FLOW_SLUGS = [
  "redes_puntaje_y_filtros",
  "facebook_reels",
  "limpieza_nombres",
  "email_hunter",
];

function initialSlugsForEditor(p: ProgramDetail): string[] {
  const sorted = [...p.criteria].sort((a, b) => a.orden - b.orden);
  const fromTpl = sorted.map((c) => c.template_slug).filter((s): s is string => Boolean(s));
  if (fromTpl.length > 0) return fromTpl;
  if (sorted.length === 0) return [...DEFAULT_FLOW_SLUGS];
  return [];
}

export function ProgramDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [program, setProgram] = useState<ProgramDetail | null>(null);
  const [catalog, setCatalog] = useState<CriterionCatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [flowEditorOpen, setFlowEditorOpen] = useState(false);
  const [flowSlugs, setFlowSlugs] = useState<string[]>([]);
  const [savingFlow, setSavingFlow] = useState(false);
  const [deletingProgram, setDeletingProgram] = useState(false);

  useEffect(() => {
    if (!id) return;
    let c = false;
    (async () => {
      try {
        const [p, cat] = await Promise.all([fetchProgram(id), fetchCriterionCatalog()]);
        if (!c) {
          setProgram(p);
          setCatalog(cat);
        }
      } catch (e) {
        await Swal.fire({
          icon: "error",
          title: "No se pudo cargar el programa",
          text: e instanceof Error ? e.message : "Error",
          customClass: { popup: "netalyst-swal" },
        });
        if (!c) setProgram(null);
      } finally {
        if (!c) setLoading(false);
      }
    })();
    return () => {
      c = true;
    };
  }, [id]);

  const catalogMap = useMemo(() => {
    const m: Record<string, CriterionCatalogItem> = {};
    catalog.forEach((x) => {
      m[x.slug] = x;
    });
    return m;
  }, [catalog]);

  const availableToAdd = useMemo(
    () => catalog.filter((t) => !flowSlugs.includes(t.slug)),
    [catalog, flowSlugs],
  );

  function openFlowEditor() {
    if (program) setFlowSlugs(initialSlugsForEditor(program));
    setFlowEditorOpen(true);
  }

  function addSlug(slug: string) {
    setFlowSlugs((prev) => [...prev, slug]);
  }

  function removeSlug(slug: string) {
    setFlowSlugs((prev) => prev.filter((s) => s !== slug));
  }

  async function saveFlow() {
    if (!id || !program) return;
    if (flowSlugs.length === 0) {
      await Swal.fire({
        icon: "warning",
        title: "Sin criterios",
        text: "Añade al menos una plantilla del catálogo.",
        customClass: { popup: "netalyst-swal" },
      });
      return;
    }
    const hadManualOnly =
      program.criteria.length > 0 && program.criteria.every((c) => !c.template_slug);
    if (hadManualOnly) {
      const r = await Swal.fire({
        icon: "warning",
        title: "Reemplazar criterios actuales",
        text:
          "Este programa tenía criterios sin plantilla del catálogo. Al guardar, se sustituirán por el flujo que definiste aquí.",
        showCancelButton: true,
        confirmButtonText: "Sí, guardar",
        cancelButtonText: "Cancelar",
        customClass: { popup: "netalyst-swal" },
      });
      if (!r.isConfirmed) return;
    }
    setSavingFlow(true);
    try {
      const updated = await replaceProgramFlow(id, { criterio_slugs: flowSlugs });
      setProgram(updated);
      setFlowEditorOpen(false);
      await Swal.fire({
        icon: "success",
        title: "Flujo actualizado",
        timer: 1800,
        showConfirmButton: false,
        customClass: { popup: "netalyst-swal" },
      });
    } catch (e) {
      await Swal.fire({
        icon: "error",
        title: "No se pudo guardar",
        text: e instanceof Error ? e.message : "Error",
        customClass: { popup: "netalyst-swal" },
      });
    } finally {
      setSavingFlow(false);
    }
  }

  async function handleDeleteProgram() {
    if (!id || !program) return;
    const r = await Swal.fire({
      icon: "warning",
      title: "¿Eliminar este programa?",
      text: `Se borrará permanentemente “${program.nombre}” y todos sus criterios y pasos. Esta acción no se puede deshacer.`,
      showCancelButton: true,
      confirmButtonText: "Sí, eliminar",
      cancelButtonText: "Cancelar",
      focusCancel: true,
      customClass: { popup: "netalyst-swal" },
    });
    if (!r.isConfirmed) return;
    setDeletingProgram(true);
    try {
      await deleteProgram(id);
      await Swal.fire({
        icon: "success",
        title: "Programa eliminado",
        timer: 1600,
        showConfirmButton: false,
        customClass: { popup: "netalyst-swal" },
      });
      navigate("/programas", { replace: true });
    } catch (e) {
      await Swal.fire({
        icon: "error",
        title: "No se pudo eliminar",
        text: e instanceof Error ? e.message : "Error",
        customClass: { popup: "netalyst-swal" },
      });
    } finally {
      setDeletingProgram(false);
    }
  }

  const preview = useMemo(() => {
    if (!program) return { entrega: [] as string[], salida: [] as string[] };
    const entrega: string[] = [];
    const salida: string[] = [];
    const sorted = [...program.criteria].sort((a, b) => a.orden - b.orden);
    for (const cr of sorted) {
      const slug = cr.template_slug;
      const tpl = slug ? catalogMap[slug] : undefined;
      if (tpl) {
        entrega.push(tpl.entrega_usuario);
        salida.push(tpl.salida_esperada);
      }
    }
    return { entrega, salida };
  }, [program, catalogMap]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-brand-dark text-slate-500">
        Cargando…
      </div>
    );
  }

  if (!program) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-brand-dark">
        <p className="text-slate-400">Programa no encontrado.</p>
        <Link to="/programas">
          <Button type="button">Volver a programas</Button>
        </Link>
      </div>
    );
  }

  const sortedCriteria = [...program.criteria].sort((a, b) => a.orden - b.orden);

  return (
    <div className="min-h-screen bg-brand-dark text-brand-white">
      <header className="border-b border-white/10 bg-slate-900/50 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-4 md:px-8">
          <Link to="/programas" className="flex items-center gap-2 text-sm text-slate-400 hover:text-brand-white">
            <img src={LOGO_URL} alt="" className="h-8 w-auto opacity-80" />
            ← Todos los programas
          </Link>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="border-red-500/35 text-red-400 hover:border-red-500/60 hover:bg-red-500/10"
            disabled={deletingProgram || flowEditorOpen}
            onClick={() => void handleDeleteProgram()}
          >
            <HiOutlineTrash className="mr-2 h-4 w-4" />
            {deletingProgram ? "Eliminando…" : "Eliminar programa"}
          </Button>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-10 md:px-8">
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-6 md:flex-row md:items-start">
          {program.image_brand_url && (
            <img
              src={program.image_brand_url}
              alt=""
              className="h-16 w-auto max-w-[200px] shrink-0 object-contain md:h-20"
            />
          )}
          <div className="min-w-0 flex-1">
            {program.brand && (
              <p className="text-sm font-semibold uppercase tracking-wide text-brand-blue">{program.brand}</p>
            )}
            <h1 className="font-display text-3xl font-bold md:text-4xl">{program.nombre}</h1>
            <p className="mt-3 max-w-3xl text-slate-400">
              {program.descripcion || "Sin descripción registrada."}
            </p>
            <div className="mt-6">
              <Link to={`/programas/${program.id}/validar`}>
                <Button type="button" className="gap-2">
                  <HiOutlinePlay className="h-4 w-4" />
                  Iniciar validación
                </Button>
              </Link>
            </div>
          </div>
        </motion.div>

        <div className="mt-10 grid gap-6 lg:grid-cols-2">
          <Card className="border-brand-blue/25">
            <CardHeader className="flex flex-row items-center gap-2 pb-2">
              <HiOutlineClipboardList className="h-5 w-5 text-brand-blue" />
              <CardTitle className="text-base">Qué debes entregar</CardTitle>
            </CardHeader>
            <CardContent>
              {preview.entrega.length === 0 ? (
                <p className="text-sm text-slate-500">
                  No hay plantilla de entregables enlazada (programa creado antes del catálogo o
                  criterios manuales). Revisa cada criterio abajo.
                </p>
              ) : (
                <ul className="space-y-3 text-sm text-slate-300">
                  {preview.entrega.map((t, i) => (
                    <li key={i} className="flex gap-2 border-l-2 border-brand-blue/50 pl-3">
                      {t}
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card className="border-brand-green/25">
            <CardHeader className="flex flex-row items-center gap-2 pb-2">
              <HiOutlineDownload className="h-5 w-5 text-brand-green" />
              <CardTitle className="text-base">Qué recibirás</CardTitle>
            </CardHeader>
            <CardContent>
              {preview.salida.length === 0 ? (
                <p className="text-sm text-slate-500">
                  Misma nota: sin plantilla enlazada. La validación sigue produciendo columnas según
                  los pasos configurados (score, exclusiones, Hunter, etc.).
                </p>
              ) : (
                <ul className="space-y-3 text-sm text-slate-300">
                  {preview.salida.map((t, i) => (
                    <li key={i} className="flex gap-2 border-l-2 border-brand-green/50 pl-3">
                      {t}
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="mt-14 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="font-display text-xl font-semibold text-brand-white">
              Flujo de criterios y pasos
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Orden de ejecución al subir un archivo a este programa. Cada paso invoca una función
              registrada en el backend.
            </p>
          </div>
          {!flowEditorOpen && catalog.length > 0 && (
            <Button type="button" variant="outline" className="shrink-0 gap-2" onClick={openFlowEditor}>
              <HiOutlinePencil className="h-4 w-4" />
              Editar flujo
            </Button>
          )}
        </div>

        {flowEditorOpen && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 space-y-6 rounded-2xl border border-brand-purple/25 bg-brand-purple/5 p-4 md:p-6"
          >
            <p className="text-sm text-slate-400">
              Añade plantillas del catálogo, arrastra para ordenar y guarda. Esto{" "}
              <strong className="text-brand-white">reemplaza</strong> todos los criterios actuales del
              programa (los pasos se regeneran desde el backend).
            </p>
            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Añadir del catálogo</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {availableToAdd.length === 0 ? (
                    <p className="text-sm text-slate-500">Todas las plantillas están en el flujo.</p>
                  ) : (
                    availableToAdd.map((t) => (
                      <div
                        key={t.slug}
                        className="flex items-start justify-between gap-3 rounded-lg border border-white/10 bg-white/[0.03] p-3"
                      >
                        <div>
                          <p className="font-medium text-brand-white">{t.nombre}</p>
                          <p className="mt-1 line-clamp-2 text-xs text-slate-500">{t.objetivo}</p>
                        </div>
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          className="shrink-0"
                          onClick={() => addSlug(t.slug)}
                        >
                          <HiOutlinePlus className="h-4 w-4" />
                        </Button>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
              <Card className="border-brand-purple/25">
                <CardHeader>
                  <CardTitle className="text-base">Orden del flujo</CardTitle>
                  <p className="text-sm text-slate-400">
                    Arrastra para reordenar. Así se ejecutarán al validar una lista.
                  </p>
                </CardHeader>
                <CardContent>
                  {flowSlugs.length === 0 ? (
                    <p className="text-sm text-slate-500">
                      Añade criterios desde la columna izquierda (o abre de nuevo si el programa solo
                      tenía criterios manuales sin plantilla).
                    </p>
                  ) : (
                    <Reorder.Group
                      axis="y"
                      values={flowSlugs}
                      onReorder={setFlowSlugs}
                      className="space-y-2"
                    >
                      {flowSlugs.map((slug) => {
                        const t = catalogMap[slug];
                        return (
                          <Reorder.Item
                            key={slug}
                            value={slug}
                            className="cursor-grab rounded-xl border border-white/10 bg-slate-800/80 p-3 active:cursor-grabbing"
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div>
                                <p className="text-xs text-brand-purple">{slug}</p>
                                <p className="font-medium text-brand-white">{t?.nombre ?? slug}</p>
                                <p className="mt-1 text-xs text-slate-500">
                                  {t?.steps.length ?? 0} pasos registrados
                                </p>
                              </div>
                              <button
                                type="button"
                                onClick={() => removeSlug(slug)}
                                className="rounded-lg p-2 text-slate-500 hover:bg-brand-red/20 hover:text-brand-red"
                                aria-label="Quitar del flujo"
                              >
                                <HiOutlineTrash className="h-5 w-5" />
                              </button>
                            </div>
                          </Reorder.Item>
                        );
                      })}
                    </Reorder.Group>
                  )}
                </CardContent>
              </Card>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button type="button" disabled={savingFlow} onClick={saveFlow}>
                {savingFlow ? "Guardando…" : "Guardar flujo"}
              </Button>
              <Button
                type="button"
                variant="ghost"
                disabled={savingFlow}
                onClick={() => setFlowEditorOpen(false)}
              >
                Cancelar
              </Button>
            </div>
          </motion.div>
        )}

        {!flowEditorOpen && (
          <div className="mt-6 space-y-6">
            {sortedCriteria.length === 0 ? (
              <Card className="border-dashed border-white/20 bg-white/[0.02]">
                <CardContent className="py-10 text-center">
                  <p className="text-slate-400">
                    Este programa aún no tiene criterios configurados (o se creó solo con cabecera).
                  </p>
                  {catalog.length > 0 && (
                    <Button type="button" className="mt-4 gap-2" onClick={openFlowEditor}>
                      <HiOutlinePlus className="h-4 w-4" />
                      Definir flujo desde el catálogo
                    </Button>
                  )}
                </CardContent>
              </Card>
            ) : (
              sortedCriteria.map((cr, idx) => (
                <motion.div
                  key={cr.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.05 * idx }}
                >
                  <Card>
                    <CardHeader className="border-b border-white/10 pb-4">
                      <div className="flex flex-wrap items-baseline gap-2">
                        <span className="rounded bg-brand-purple/20 px-2 py-0.5 font-mono text-xs text-brand-purple">
                          Orden {cr.orden}
                        </span>
                        {cr.template_slug && (
                          <span className="text-xs text-slate-500">slug: {cr.template_slug}</span>
                        )}
                      </div>
                      <CardTitle className="mt-2 text-lg">{cr.nombre}</CardTitle>
                      {cr.objetivo && <p className="text-sm text-slate-400">{cr.objetivo}</p>}
                    </CardHeader>
                    <CardContent className="pt-4">
                      <ol className="space-y-2">
                        {[...cr.steps]
                          .sort((a, b) => a.paso_num - b.paso_num)
                          .map((st) => (
                            <li
                              key={st.id}
                              className="flex flex-col gap-1 rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2 sm:flex-row sm:items-center sm:justify-between"
                            >
                              <div>
                                <span className="text-xs text-brand-pink">Paso {st.paso_num}</span>
                                <p className="font-medium text-brand-white">{st.nombre}</p>
                                {st.definicion && (
                                  <p className="text-xs text-slate-500">{st.definicion}</p>
                                )}
                              </div>
                              <code className="mt-1 shrink-0 rounded bg-slate-800 px-2 py-1 text-xs text-brand-yellow sm:mt-0">
                                {st.funcion_a_ejecutar}
                              </code>
                            </li>
                          ))}
                      </ol>
                    </CardContent>
                  </Card>
                </motion.div>
              ))
            )}
          </div>
        )}
      </main>
    </div>
  );
}
