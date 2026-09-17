import type { HTMLAttributes } from "react";

import { cn } from "@/lib/cn";

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  tone?: "accent" | "neutral";
};

const toneClasses = {
  accent:
    "border-amber-300/25 bg-amber-300/10 text-amber-100 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]",
  neutral: "border-white/10 bg-white/[0.04] text-zinc-300",
} as const;

export function Badge({ className, tone = "neutral", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-3 py-1 font-mono text-[0.66rem] font-semibold tracking-[0.18em] uppercase",
        toneClasses[tone],
        className,
      )}
      {...props}
    />
  );
}
