"use client";

export default function LibraryError({ reset }: { reset: () => void }) {
  return (
    <main className="grid min-h-screen place-items-center bg-background px-5 text-center text-foreground">
      <div>
        <p className="font-serif text-4xl text-white">Não foi possível abrir sua biblioteca.</p>
        <p className="mt-3 text-sm text-zinc-500">Nenhum dado privado foi perdido. Tente novamente.</p>
        <button className="mt-7 rounded-xl bg-amber-300 px-5 py-3 font-semibold text-zinc-950" onClick={reset} type="button">Tentar novamente</button>
      </div>
    </main>
  );
}
