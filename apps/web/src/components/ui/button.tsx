import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

type ButtonVariant = "primary" | "secondary";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
};

const baseClasses =
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-full px-5 py-2.5 text-sm font-semibold transition duration-200 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-amber-300 disabled:cursor-not-allowed disabled:opacity-45";

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-amber-300 text-zinc-950 shadow-[0_12px_40px_rgba(252,211,77,0.16)] hover:bg-amber-200",
  secondary:
    "border border-white/12 bg-white/[0.045] text-zinc-100 hover:border-white/25 hover:bg-white/[0.08]",
};

export function buttonClassName(
  variant: ButtonVariant = "primary",
  className?: string,
): string {
  return cn(baseClasses, variantClasses[variant], className);
}

export function Button({
  className,
  type = "button",
  variant = "primary",
  ...props
}: ButtonProps) {
  return (
    <button
      className={buttonClassName(variant, className)}
      type={type}
      {...props}
    />
  );
}
