import Link from "next/link";

export default function OfflinePage() {
  return (
    <main className="grid min-h-screen place-items-center bg-background px-6 text-center text-foreground">
      <div>
        <p className="font-mono text-xs tracking-[0.22em] text-amber-200 uppercase">Offline</p>
        <h1 className="mt-4 font-serif text-5xl text-white">O projetor ficou sem rede.</h1>
        <p className="mx-auto mt-5 max-w-lg text-sm leading-7 text-zinc-400">
          O Matinê não guarda sua biblioteca, diário ou reviews no cache do service worker.
          Reconecte para acessar seus dados privados.
        </p>
        <Link className="mt-8 inline-flex rounded-xl bg-amber-300 px-5 py-3 font-semibold text-zinc-950" href="/">
          Tentar novamente
        </Link>
      </div>
    </main>
  );
}
