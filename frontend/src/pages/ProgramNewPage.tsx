import { Reorder, motion } from "framer-motion";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { HiOutlineTrash, HiOutlinePlus } from "react-icons/hi";
import { Link, useNavigate } from "react-router-dom";
import Swal from "sweetalert2";
import type { CriterionCatalogItem } from "@/api/programs";
import { createProgramFromFlow, fetchCriterionCatalog } from "@/api/programs";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { LOGO_URL } from "@/lib/constants";

const DEFAULT_SLUGS = [
  "redes_puntaje_y_filtros",
  "facebook_reels",
  "limpieza_nombres",
  "email_hunter",
];

export function ProgramNewPage() {
  const navigate = useNavigate();
  const [catalog, setCatalog] = useState<CriterionCatalogItem[]>([]);
  const [nombre, setNombre] = useState("");
  const [brand, setBrand] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [orderedSlugs, setOrderedSlugs] = useState<string[]>(DEFAULT_SLUGS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let c = false;
    (async () => {
      try {
        const data = await fetchCriterionCatalog();
        if (!c) setCatalog(data);
      } catch (e) {
        await Swal.fire({
          icon: "error",
          title: "Catálogo no disponible",
          text: e instanceof Error ? e.message : "Error",
          customClass: { popup: "netalyst-swal" },
        });
      } finally {
        if (!c) setLoading(false);
      }
    })();
    return () => {
      c = true;
    };
  }, []);

  const bySlug = useMemo(() => {
    const m: Record<string, CriterionCatalogItem> = {};
    catalog.forEach((t) => {
      m[t.slug] = t;
    });
    return m;
  }, [catalog]);

  const availableToAdd = useMemo(
    () => catalog.filter((t) => !orderedSlugs.includes(t.slug)),
    [catalog, orderedSlugs],
  );

  function addSlug(slug: string) {
    setOrderedSlugs((prev) => [...prev, slug]);
  }

  function removeSlug(slug: string) {
    setOrderedSlugs((prev) => prev.filter((s) => s !== slug));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!nombre.trim()) {
      await Swal.fire({
        icon: "warning",
        title: "Nombre obligatorio",
        text: "Indica el nombre del programa u oportunidad.",
        customClass: { popup: "netalyst-swal" },
      });
      return;
    }
    if (orderedSlugs.length === 0) {
      await Swal.fire({
        icon: "warning",
        title: "Sin criterios",
        text: "Añade al menos un criterio del catálogo al flujo.",
        customClass: { popup: "netalyst-swal" },
      });
      return;
    }
    setSaving(true);
    try {
      const created = await createProgramFromFlow({
        nombre: nombre.trim(),
        brand: brand.trim() || null,
        descripcion: descripcion.trim() || null,
        image_brand_url: imageUrl.trim() || null,
        is_active: true,
        criterio_slugs: orderedSlugs,
      });
      await Swal.fire({
        icon: "success",
        title: "Programa creado",
        text: "Ya puedes revisar el flujo y los entregables.",
        timer: 2000,
        showConfirmButton: false,
        customClass: { popup: "netalyst-swal" },
      });
      navigate(`/programas/${created.id}`, { replace: true });
    } catch (err) {
      await Swal.fire({
        icon: "error",
        title: "No se pudo crear",
        text: err instanceof Error ? err.message : "Error",
        customClass: { popup: "netalyst-swal" },
      });
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="min-h-screen bg-brand-dark text-brand-white">
      <header className="border-b border-white/10 bg-slate-900/50 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 md:px-8">
          <Link to="/programas" className="flex items-center gap-2 text-sm text-slate-400 hover:text-brand-white">
            <img src={LOGO_URL} alt="" className="h-8 w-auto opacity-80" />
            ← Programas
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-10 md:px-8">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="font-display text-3xl font-bold">Nuevo programa u oportunidad</h1>
          <p className="mt-2 max-w-3xl text-slate-400">
            Registra solo la cabecera del programa y marca qué validaciones del catálogo backend
            quieres encadenar. El orden del flujo es el orden de ejecución al validar un archivo.
          </p>
        </motion.div>

        {loading ? (
          <p className="mt-10 text-slate-500">Cargando catálogo…</p>
        ) : (
          <form onSubmit={onSubmit} className="mt-10 grid gap-10 lg:grid-cols-2">
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Datos del programa</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="mb-1 block text-xs uppercase text-slate-500">Nombre *</label>
                    <Input
                      value={nombre}
                      onChange={(e) => setNombre(e.target.value)}
                      placeholder="Ej. Creator Fast Track Q2"
                      required
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-xs uppercase text-slate-500">Marca / cliente</label>
                    <Input value={brand} onChange={(e) => setBrand(e.target.value)} placeholder="Opcional" />
                  </div>
                  <div>
                    <label className="mb-1 block text-xs uppercase text-slate-500">Descripción</label>
                    <textarea
                      className="min-h-[100px] w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-brand-white placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-purple/60"
                      value={descripcion}
                      onChange={(e) => setDescripcion(e.target.value)}
                      placeholder="Contexto del programa para tu equipo…"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-xs uppercase text-slate-500">
                      URL logo marca
                    </label>
                    <Input
                      value={imageUrl}
                      onChange={(e) => setImageUrl(e.target.value)}
                      placeholder="https://…"
                    />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Añadir criterios del catálogo</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {availableToAdd.length === 0 ? (
                    <p className="text-sm text-slate-500">Todos los criterios están en el flujo.</p>
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
            </div>

            <div>
              <Card className="border-brand-purple/25">
                <CardHeader>
                  <CardTitle>Orden del flujo</CardTitle>
                  <p className="text-sm text-slate-400">
                    Arrastra para reordenar. Así se ejecutarán los criterios al validar una lista.
                  </p>
                </CardHeader>
                <CardContent>
                  <Reorder.Group axis="y" values={orderedSlugs} onReorder={setOrderedSlugs} className="space-y-2">
                    {orderedSlugs.map((slug) => {
                      const t = bySlug[slug];
                      return (
                        <Reorder.Item
                          key={slug}
                          value={slug}
                          className="cursor-grab rounded-xl border border-white/10 bg-slate-800/80 p-3 active:cursor-grabbing"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <p className="text-xs text-brand-purple">{slug}</p>
                              <p className="font-medium text-brand-white">
                                {t?.nombre ?? slug}
                              </p>
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
                </CardContent>
              </Card>

              <div className="mt-6 flex flex-wrap gap-3">
                <Button type="submit" disabled={saving}>
                  {saving ? "Guardando…" : "Crear programa"}
                </Button>
                <Link to="/programas">
                  <Button type="button" variant="ghost">
                    Cancelar
                  </Button>
                </Link>
              </div>
            </div>
          </form>
        )}
      </main>
    </div>
  );
}
