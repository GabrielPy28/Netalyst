import { motion } from "framer-motion";
import { useEffect, useState, type MouseEvent } from "react";
import { HiOutlinePlay, HiOutlinePlus, HiOutlineTrash, HiOutlineViewGrid } from "react-icons/hi";
import { Link } from "react-router-dom";
import Swal from "sweetalert2";
import type { ProgramListItem } from "@/api/programs";
import { deleteProgram, fetchPrograms } from "@/api/programs";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { LOGO_URL } from "@/lib/constants";
import { getUser } from "@/lib/authStorage";

export function ProgramsPage() {
  const user = getUser();
  const [programs, setPrograms] = useState<ProgramListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function handleDeleteProgram(p: ProgramListItem, e: MouseEvent<HTMLButtonElement>) {
    e.preventDefault();
    e.stopPropagation();
    const r = await Swal.fire({
      icon: "warning",
      title: "¿Eliminar este programa?",
      text: `Se borrará permanentemente “${p.nombre}” y todos sus criterios y pasos. Esta acción no se puede deshacer.`,
      showCancelButton: true,
      confirmButtonText: "Sí, eliminar",
      cancelButtonText: "Cancelar",
      focusCancel: true,
      customClass: { popup: "netalyst-swal" },
    });
    if (!r.isConfirmed) return;
    setDeletingId(p.id);
    try {
      await deleteProgram(p.id);
      setPrograms((prev) => prev.filter((x) => x.id !== p.id));
      await Swal.fire({
        icon: "success",
        title: "Programa eliminado",
        timer: 1800,
        showConfirmButton: false,
        customClass: { popup: "netalyst-swal" },
      });
    } catch (err) {
      await Swal.fire({
        icon: "error",
        title: "No se pudo eliminar",
        text: err instanceof Error ? err.message : "Error",
        customClass: { popup: "netalyst-swal" },
      });
    } finally {
      setDeletingId(null);
    }
  }

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchPrograms();
        if (!cancelled) setPrograms(data);
      } catch (e) {
        await Swal.fire({
          icon: "error",
          title: "No se pudieron cargar los programas",
          text: e instanceof Error ? e.message : "Error desconocido",
          customClass: { popup: "netalyst-swal" },
        });
        if (!cancelled) setPrograms([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="min-h-screen bg-brand-dark text-brand-white">
      <header className="border-b border-white/10 bg-slate-900/50 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 md:px-8">
          <Link to="/welcome" className="flex items-center gap-3 transition hover:opacity-90">
            <img src={LOGO_URL} alt="La Neta" className="h-9 w-auto" />
            <div>
              <p className="font-display text-sm font-semibold">Netalyst</p>
              <p className="text-xs text-slate-500">Programas & oportunidades</p>
            </div>
          </Link>
          <span className="hidden text-sm text-slate-400 sm:inline">{user?.name}</span>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-10 md:px-8">
        <div className="mb-10 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-2 inline-flex items-center gap-2 text-brand-purple"
            >
              <HiOutlineViewGrid className="h-5 w-5" />
              <span className="text-sm font-medium uppercase tracking-wide">Validación</span>
            </motion.div>
            <h1 className="font-display text-3xl font-bold md:text-4xl">
              Programas & oportunidades
            </h1>
            <p className="mt-2 max-w-2xl text-slate-400">
              Cada tarjeta es un flujo de criterios preconfigurado en el sistema. Elige un programa
              para ver qué validaciones aplica, qué debes subir y qué obtendrás al final. También
              puedes dar de alta un programa nuevo combinando los criterios del catálogo.
            </p>
          </div>
          <Link to="/welcome" className="shrink-0">
            <Button type="button" variant="ghost" className="border border-white/15">
              ← Volver al inicio
            </Button>
          </Link>
        </div>

        {loading ? (
          <p className="text-center text-slate-500">Cargando programas…</p>
        ) : (
          <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
            <motion.div
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.25 }}
            >
              <Link to="/programas/nuevo" className="block h-full">
                <Card className="group h-full min-h-[220px] border-2 border-dashed border-brand-purple/50 bg-brand-purple/5 transition hover:border-brand-purple hover:bg-brand-purple/10">
                  <CardContent className="flex h-full flex-col items-center justify-center gap-3 py-10 text-center">
                    <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-purple/20 text-brand-purple transition group-hover:scale-105">
                      <HiOutlinePlus className="h-8 w-8" />
                    </div>
                    <p className="font-display text-lg font-semibold text-brand-white">
                      Nuevo programa u oportunidad
                    </p>
                    <p className="max-w-xs text-sm text-slate-400">
                      Define nombre, marca y el orden de criterios (redes, Facebook, nombres, email…)
                      desde el catálogo pre-registrado.
                    </p>
                  </CardContent>
                </Card>
              </Link>
            </motion.div>

            {programs.map((p, i) => (
              <motion.div
                key={p.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 * i, duration: 0.3 }}
              >
                <Card className="flex h-full min-h-[220px] flex-col border-white/10 transition hover:border-brand-blue/40">
                  <Link to={`/programas/${p.id}`} className="flex flex-1 flex-col">
                    <CardContent className="flex flex-1 flex-col pt-2">
                      <div className="mb-3 flex items-start justify-between gap-2">
                        {p.image_brand_url ? (
                          <img
                            src={p.image_brand_url}
                            alt=""
                            className="h-10 max-w-[120px] object-contain"
                          />
                        ) : (
                          <span className="rounded-md bg-white/10 px-2 py-1 text-xs text-slate-400">
                            Sin logo
                          </span>
                        )}
                        <span className="shrink-0 rounded-full bg-brand-purple/20 px-2.5 py-0.5 text-xs font-medium text-brand-purple">
                          {p.criterios_count} criterios
                        </span>
                      </div>
                      <h2 className="font-display text-lg font-semibold text-brand-white">{p.nombre}</h2>
                      {p.brand && (
                        <p className="text-xs font-medium uppercase tracking-wide text-brand-blue">
                          {p.brand}
                        </p>
                      )}
                      <p className="mt-2 line-clamp-3 flex-1 text-sm text-slate-400">
                        {p.descripcion || "Sin descripción. Abre la vista de detalle para ver el flujo."}
                      </p>
                      <span className="mt-4 text-sm font-medium text-brand-pink">
                        Ver flujo y entregables →
                      </span>
                    </CardContent>
                  </Link>
                  <div className="flex flex-col gap-2 border-t border-white/10 px-4 py-3">
                    <Link to={`/programas/${p.id}/validar`} className="block">
                      <Button type="button" size="sm" className="w-full gap-2">
                        <HiOutlinePlay className="h-4 w-4" />
                        Iniciar validación
                      </Button>
                    </Link>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="w-full border-red-500/35 text-red-400 hover:border-red-500/60 hover:bg-red-500/10"
                      disabled={deletingId === p.id}
                      onClick={(e) => void handleDeleteProgram(p, e)}
                    >
                      <HiOutlineTrash className="mr-2 h-4 w-4" />
                      {deletingId === p.id ? "Eliminando…" : "Eliminar programa"}
                    </Button>
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        )}

        {!loading && programs.length === 0 && (
          <p className="mt-8 text-center text-slate-500">
            Aún no hay programas activos. Crea el primero con la tarjeta morada.
          </p>
        )}
      </main>
    </div>
  );
}
