"use client";

import type { ButtonHTMLAttributes, ReactNode } from "react";
import { useFormStatus } from "react-dom";

import { buttonClassName } from "@/components/ui/button";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  pendingLabel?: string;
  variant?: "primary" | "secondary";
};

export function SubmitButton({
  children,
  pendingLabel = "Salvando...",
  variant = "primary",
  className,
  disabled,
  ...props
}: Props) {
  const { pending } = useFormStatus();

  return (
    <button
      aria-busy={pending}
      className={buttonClassName(
        variant,
        className,
      )}
      disabled={pending || disabled}
      type="submit"
      {...props}
    >
      {pending ? (
        <>
          <span
            aria-hidden="true"
            className="size-3.5 animate-spin rounded-full border-2 border-current border-r-transparent"
          />
          <span>{pendingLabel}</span>
        </>
      ) : (
        children
      )}
    </button>
  );
}
