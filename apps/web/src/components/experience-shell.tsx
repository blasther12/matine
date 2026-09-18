import Link from "next/link";
import type { ReactNode } from "react";

const links = [
  ["/library", "Biblioteca"],
  ["/diary", "Diário"],
  ["/reviews", "Reviews"],
  ["/lists", "Listas"],
  ["/social", "Social"],
  ["/streaming", "Streaming"],
  ["/circles", "Círculos"],
  ["/recommendations", "Para você"],
  ["/stats", "Stats"],
  ["/wrapped", "Wrapped"],
] as const;

export function ExperienceShell({
  title,
  eyebrow,
  children,
}: {
  title: string;
  eyebrow: string;
  children: ReactNode;
}) {
  return (
    <main className="film-grain min-h-screen bg-background text-foreground">
      <header className="border-b border-white/[0.07] bg-background/90">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-5 px-5 py-5 sm:px-8 lg:px-10">
          <Link className="font-serif text-2xl text-white" href="/">Matinê</Link>
          <nav className="flex flex-1 flex-wrap gap-x-4 gap-y-2 text-xs text-zinc-400" aria-label="Área privada">
            {links.map(([href, label]) => (
              <Link className="hover:text-amber-200" href={href} key={href}>{label}</Link>
            ))}
          </nav>
        </div>
      </header>
      <section className="cinema-grid border-b border-white/[0.07]">
        <div className="mx-auto max-w-7xl px-5 py-12 sm:px-8 lg:px-10">
          <p className="font-mono text-xs tracking-[0.22em] text-amber-200 uppercase">{eyebrow}</p>
          <h1 className="mt-4 font-serif text-5xl text-white sm:text-6xl">{title}</h1>
        </div>
      </section>
      <div className="mx-auto max-w-7xl px-5 py-10 sm:px-8 lg:px-10">{children}</div>
    </main>
  );
}

export function Panel({ children }: { children: ReactNode }) {
  return <section className="rounded-2xl border border-white/10 bg-white/[0.025] p-5 sm:p-6">{children}</section>;
}

export const fieldClass =
  "mt-2 w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none focus:border-amber-300";
export const buttonClass =
  "rounded-xl bg-amber-300 px-4 py-3 text-sm font-semibold text-zinc-950 hover:bg-amber-200";
