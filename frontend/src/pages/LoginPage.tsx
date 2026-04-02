import { motion } from "framer-motion";
import { FormEvent, useEffect, useState } from "react";
import { FcGoogle } from "react-icons/fc";
import { HiOutlineMail, HiOutlineLockClosed } from "react-icons/hi";
import { useNavigate } from "react-router-dom";
import Swal from "sweetalert2";
import { loginRequest } from "@/api/auth";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { LOGO_URL } from "@/lib/constants";
import { getToken, setSession } from "@/lib/authStorage";

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (getToken()) navigate("/welcome", { replace: true });
  }, [navigate]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await loginRequest({ email: email.trim(), password });
      setSession(res.access_token, res.user);
      await Swal.fire({
        icon: "success",
        title: "¡Bienvenido!",
        text: `Hola, ${res.user.name || res.user.email}`,
        timer: 1800,
        showConfirmButton: false,
        customClass: { popup: "netalyst-swal" },
      });
      navigate("/welcome", { replace: true });
    } catch (err) {
      await Swal.fire({
        icon: "error",
        title: "No pudimos iniciar sesión",
        text: err instanceof Error ? err.message : "Revisa tus credenciales.",
        confirmButtonText: "Entendido",
        customClass: { popup: "netalyst-swal" },
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-brand-dark">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(102,65,237,0.35),transparent)]" />
      <div className="pointer-events-none absolute -left-32 top-1/3 h-96 w-96 rounded-full bg-brand-pink/15 blur-[100px]" />
      <div className="pointer-events-none absolute -right-20 bottom-0 h-80 w-80 rounded-full bg-brand-blue/20 blur-[90px]" />

      <div className="relative z-10 mx-auto flex min-h-screen max-w-6xl flex-col gap-10 px-4 py-10 md:flex-row md:items-center md:justify-between md:px-8 lg:px-12">
        <motion.div
          className="max-w-xl flex-1 space-y-6"
          initial={{ opacity: 0, x: -24 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          <img
            src={LOGO_URL}
            alt="La Neta"
            className="h-14 w-auto object-contain md:h-16"
          />
          <h1 className="font-display text-3xl font-bold leading-tight text-brand-white md:text-4xl lg:text-5xl">
            Netalyst: validación de creadores,{" "}
            <span className="bg-gradient-to-r from-brand-blue via-brand-purple to-brand-pink bg-clip-text text-transparent">
              sin fricción
            </span>
          </h1>
          <p className="text-lg leading-relaxed text-slate-300">
            Plataforma interna de <strong className="text-brand-white">La Neta</strong> para
            limpiar listas, aplicar criterios por programa u oportunidad y priorizar creadores con
            datos confiables. Centraliza redes sociales, reglas de exclusión, puntuación y correo en
            un solo flujo: menos hojas sueltas, más decisiones claras cada día.
          </p>
          <ul className="grid gap-3 text-sm text-slate-400 sm:grid-cols-2">
            {[
              "Listas CSV/Excel con resultados válidos vs excluidos",
              "Puntaje 0–16 y umbrales por negocio",
              "Integración con verificación de email (Hunter)",
              "Diseñado para equipos que viven del detalle",
            ].map((t) => (
              <li
                key={t}
                className="flex items-start gap-2 rounded-lg border border-white/5 bg-white/[0.03] px-3 py-2"
              >
                <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-green" />
                {t}
              </li>
            ))}
          </ul>
        </motion.div>

        <motion.div
          className="w-full max-w-md flex-1"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.1 }}
        >
          <Card className="border-brand-purple/20">
            <CardHeader>
              <CardTitle>Iniciar sesión</CardTitle>
              <CardDescription>
                Usa el correo corporativo autorizado en Supabase Auth.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={onSubmit} className="space-y-4">
                <div className="space-y-2">
                  <label className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Correo
                  </label>
                  <div className="relative">
                    <HiOutlineMail className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-500" />
                    <Input
                      type="email"
                      autoComplete="email"
                      placeholder="tu@empresa.com"
                      className="pl-10"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Contraseña
                  </label>
                  <div className="relative">
                    <HiOutlineLockClosed className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-500" />
                    <Input
                      type="password"
                      autoComplete="current-password"
                      placeholder="••••••••"
                      className="pl-10"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                  </div>
                </div>
                <Button type="submit" className="w-full" disabled={loading}>
                  {loading ? "Entrando…" : "Entrar"}
                </Button>
              </form>
              <p className="mt-4 flex items-center justify-center gap-2 text-center text-xs text-slate-500">
                <FcGoogle className="h-4 w-4" />
                El acceso con Google u otros proveedores se puede habilitar desde Supabase cuando lo
                definan.
              </p>
            </CardContent>
          </Card>
          <p className="mt-6 text-center text-xs text-slate-600">
            ¿Problemas para entrar? Solicita acceso al equipo{" "}
            <span className="text-brand-blue">La Neta</span>.
          </p>
        </motion.div>
      </div>
    </div>
  );
}
