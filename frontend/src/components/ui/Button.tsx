import { type ButtonHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost" | "outline";
  size?: "default" | "sm" | "lg";
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "default", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-purple focus-visible:ring-offset-2 focus-visible:ring-offset-brand-dark disabled:pointer-events-none disabled:opacity-50",
          variant === "primary" &&
            "bg-brand-purple text-white shadow-lg shadow-brand-purple/30 hover:bg-brand-purple/90 hover:shadow-glow",
          variant === "ghost" &&
            "bg-white/5 text-brand-white hover:bg-white/10 border border-white/10",
          variant === "outline" &&
            "border-2 border-brand-purple/60 bg-transparent text-brand-purple hover:bg-brand-purple/10",
          size === "default" && "h-11 px-5 py-2 text-sm",
          size === "sm" && "h-9 px-3 text-xs",
          size === "lg" && "h-12 px-8 text-base",
          className,
        )}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";
