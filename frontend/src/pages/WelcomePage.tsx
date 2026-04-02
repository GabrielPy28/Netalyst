import { motion } from "framer-motion";
import {
  HiOutlineChartBar,
  HiOutlineCloudUpload,
  HiOutlineMail,
  HiOutlineShieldCheck,
  HiOutlineSparkles,
} from "react-icons/hi";
import { Link, useNavigate } from "react-router-dom";
import Swal from "sweetalert2";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { LOGO_URL } from "@/lib/constants";
import { clearSession, getUser } from "@/lib/authStorage";

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: 0.08 * i, duration: 0.45 },
  }),
};

export function WelcomePage() {
  const navigate = useNavigate();
  const user = getUser();

  async function handleLogout() {
    const r = await Swal.fire({
      title: "¿Cerrar sesión?",
      icon: "question",
      showCancelButton: true,
      confirmButtonText: "Salir",
      cancelButtonText: "Cancelar",
      customClass: { popup: "netalyst-swal" },
    });
    if (r.isConfirmed) {
      clearSession();
      navigate("/login", { replace: true });
    }
  }

  const tiles = [
    {
      icon: HiOutlineCloudUpload,
      title: "Carga y validación",
      text: "Sube CSV o Excel, ejecuta el programa activo y obtén dos salidas: creadores válidos y excluidos, con motivo y etapa del filtro.",
      color: "text-brand-blue",
      bg: "bg-brand-blue/10",
    },
    {
      icon: HiOutlineChartBar,
      title: "Puntaje y redes",
      text: "Actualiza datos desde Instagram, TikTok y YouTube, aplica el score 0–16, umbrales de seguidores y detecta la cuenta principal automáticamente.",
      color: "text-brand-purple",
      bg: "bg-brand-purple/10",
    },
    {
      icon: HiOutlineShieldCheck,
      title: "Reglas de negocio",
      text: "Facebook Reels recientes, limpieza de nombres y verificación Hunter se encadenan en el orden que definas para cada oportunidad.",
      color: "text-brand-pink",
      bg: "bg-brand-pink/10",
    },
    {
      icon: HiOutlineMail,
      title: "Correo confiable",
      text: "Hunter.io valida direcciones al final del flujo para que solo avancen contactos que cumplen tu política de calidad.",
      color: "text-brand-green",
      bg: "bg-brand-green/10",
    },
  ];

  return (
    <div className="min-h-screen bg-brand-dark text-brand-white">
      <header className="border-b border-white/10 bg-slate-900/50 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 md:px-8">
          <div className="flex items-center gap-3">
            <img src={LOGO_URL} alt="La Neta" className="h-10 w-auto" />
            <div>
              <p className="font-display text-sm font-semibold text-brand-white">Netalyst</p>
              <p className="text-xs text-slate-500">La Neta · Creator validation</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden text-right text-sm text-slate-400 sm:block">
              <span className="block font-medium text-brand-white">
                {user?.name || "Usuario"}
              </span>
              <span className="text-xs">{user?.email}</span>
            </span>
            <Button type="button" variant="outline" size="sm" onClick={handleLogout}>
              Salir
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-12 md:px-8">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12 text-center md:text-left"
        >
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-brand-purple/30 bg-brand-purple/10 px-4 py-1.5 text-xs font-medium text-brand-purple">
            <HiOutlineSparkles className="h-4 w-4" />
            Herramienta operativa para tu día a día
          </div>
          <h1 className="font-display text-3xl font-bold tracking-tight md:text-5xl">
            Hola{user?.name ? `, ${user.name.split(" ")[0]}` : ""}. Esto es lo que{" "}
            <span className="bg-gradient-to-r from-brand-blue to-brand-pink bg-clip-text text-transparent">
              Netalyst
            </span>{" "}
            hace por ti
          </h1>
          <p className="mt-4 max-w-3xl text-lg leading-relaxed text-slate-400">
            Cada mañana recibes listas de creadores distintas: campañas distintas, criterios distintos,
            urgencias distintas. Esta plataforma te ahorra el caos de copiar y pegar entre hojas,
            APIs y correos: <strong className="text-brand-white">un solo lugar</strong> donde subes el
            archivo, corres el programa correcto y descargas quién pasó, quién no y por qué. Menos
            errores manuales, más tiempo para estrategia y relación con talento.
          </p>
        </motion.div>

        <div className="grid gap-4 sm:grid-cols-2">
          {tiles.map((tile, i) => (
            <motion.div key={tile.title} custom={i} variants={fadeUp} initial="hidden" animate="show">
              <Card className="h-full border-white/10 transition hover:border-brand-purple/25">
                <CardContent className="flex gap-4 pt-2">
                  <div
                    className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${tile.bg}`}
                  >
                    <tile.icon className={`h-6 w-6 ${tile.color}`} />
                  </div>
                  <div>
                    <h2 className="font-display text-lg font-semibold text-brand-white">{tile.title}</h2>
                    <p className="mt-1 text-sm leading-relaxed text-slate-400">{tile.text}</p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-12 rounded-2xl border border-brand-yellow/20 bg-gradient-to-br from-brand-yellow/10 via-transparent to-brand-purple/10 p-8 text-center md:text-left"
        >
          <p className="font-display text-lg font-semibold text-brand-white">
            Programas y oportunidades
          </p>
          <p className="mt-2 max-w-2xl text-sm text-slate-400">
            Define o revisa cada oportunidad: nombre, marca y el orden de validaciones (redes, Reels,
            limpieza, Hunter). Cada criterio usa plantillas ya registradas en el sistema.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link to="/programas">
              <Button type="button" variant="primary">
                Validación por programas y oportunidades
              </Button>
            </Link>
            <Button className="opacity-70" type="button" variant="outline" disabled>
              Subir archivo (próximamente)
            </Button>
          </div>
        </motion.div>
      </main>
    </div>
  );
}
