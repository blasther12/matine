"use client";

import Link from "next/link";

import { buttonClassName } from "@/components/ui/button";

export default function MovieError() {
  return (
    <main className="grid min-h-screen place-items-center bg-background px-6 text-center">
      <div>
        <p className="font-mono text-xs tracking-widest text-red-300 uppercase">Catálogo indisponível</p>
        <h1 className="mt-4 font-serif text-5xl text-white">A sessão foi interrompida.</h1>
        <p className="mt-4 text-zinc-500">Não conseguimos carregar este filme agora. Tente novamente em instantes.</p>
        <Link className={buttonClassName("secondary", "mt-8")} href="/search">
          Voltar à busca
        </Link>
      </div>
    </main>
  );
}
