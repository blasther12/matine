import Link from "next/link";
import { connection } from "next/server";

import { Badge } from "@/components/ui/badge";
import { buttonClassName } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { foundationPillars, privacyPrinciples } from "@/lib/foundation";

function ArrowIcon() {
  return (
    <svg
      aria-hidden="true"
      className="size-4"
      fill="none"
      viewBox="0 0 24 24"
    >
      <path
        d="M5 12h14m-5-5 5 5-5 5"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.7"
      />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg
      aria-hidden="true"
      className="size-4"
      fill="none"
      viewBox="0 0 24 24"
    >
      <path
        d="m5 12 4 4L19 6"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function FilmFrames() {
  return (
    <div
      aria-hidden="true"
      className="relative mx-auto h-[27rem] w-full max-w-[31rem] sm:h-[32rem]"
    >
      <div className="poster-card poster-card-left absolute top-16 left-[3%] h-72 w-44 -rotate-[9deg] rounded-[1.35rem] border border-white/10 bg-[linear-gradient(150deg,#22252b_0%,#111318_58%,#08090b_100%)] p-4 shadow-2xl sm:h-80 sm:w-52">
        <div className="h-full rounded-[1rem] border border-white/[0.06] bg-[radial-gradient(circle_at_45%_32%,#a16207_0%,#451a03_27%,#09090b_68%)]">
          <div className="flex h-full flex-col justify-end p-4">
            <span className="font-mono text-[0.55rem] tracking-[0.32em] text-amber-100/60 uppercase">
              Tonight
            </span>
            <span className="mt-2 font-serif text-2xl leading-none text-zinc-100">
              After the
              <br /> last light
            </span>
          </div>
        </div>
      </div>

      <div className="poster-card poster-card-right absolute top-8 right-[2%] h-72 w-44 rotate-[8deg] rounded-[1.35rem] border border-white/10 bg-[linear-gradient(150deg,#202329_0%,#101116_62%,#08090b_100%)] p-4 shadow-2xl sm:h-80 sm:w-52">
        <div className="h-full rounded-[1rem] border border-white/[0.06] bg-[radial-gradient(ellipse_at_52%_30%,#334155_0%,#172033_25%,#08090b_68%)]">
          <div className="flex h-full flex-col justify-end p-4">
            <span className="font-mono text-[0.55rem] tracking-[0.32em] text-sky-100/60 uppercase">
              Shared pick
            </span>
            <span className="mt-2 font-serif text-2xl leading-none text-zinc-100">
              A quiet
              <br /> orbit
            </span>
          </div>
        </div>
      </div>

      <div className="poster-card poster-card-center absolute top-0 left-1/2 h-[23rem] w-56 -translate-x-1/2 rounded-[1.5rem] border border-amber-200/20 bg-[linear-gradient(155deg,#2a2017_0%,#16110d_48%,#070708_100%)] p-4 shadow-[0_34px_100px_rgba(0,0,0,0.72),0_0_80px_rgba(217,119,6,0.09)] sm:h-[27rem] sm:w-64">
        <div className="cinema-poster h-full overflow-hidden rounded-[1.1rem] border border-white/[0.07]">
          <div className="flex h-full flex-col justify-between p-5">
            <div className="flex items-center justify-between font-mono text-[0.52rem] tracking-[0.24em] text-zinc-400 uppercase">
              <span>For you</span>
              <span>01</span>
            </div>
            <div>
              <div className="mb-4 h-px w-10 bg-amber-200/60" />
              <p className="font-serif text-[2rem] leading-[0.92] tracking-[-0.03em] text-white sm:text-[2.35rem]">
                The film
                <br /> for this
                <br /> moment
              </p>
              <p className="mt-4 max-w-36 text-[0.65rem] leading-relaxed text-zinc-400">
                Taste, time and context — together.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="absolute right-1 bottom-4 rounded-2xl border border-white/10 bg-zinc-950/85 px-4 py-3 shadow-2xl backdrop-blur-xl sm:right-3 sm:bottom-8">
        <p className="font-mono text-[0.56rem] tracking-[0.22em] text-zinc-500 uppercase">
          Why this movie?
        </p>
        <p className="mt-1.5 text-xs text-zinc-200">Disponível · 104 min · gosto em comum</p>
      </div>
    </div>
  );
}

export default async function HomePage() {
  // A per-request CSP nonce requires dynamic rendering in Next.js.
  await connection();

  return (
    <div className="film-grain min-h-screen overflow-hidden bg-background text-foreground">
      <a
        className="fixed top-3 left-3 z-50 -translate-y-24 rounded-full bg-amber-300 px-4 py-2 text-sm font-semibold text-zinc-950 transition focus:translate-y-0"
        href="#main-content"
      >
        Ir para o conteúdo
      </a>

      <header className="relative z-30 border-b border-white/[0.07] bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-5 sm:px-8 lg:px-10">
          <Link
            aria-label="Matinê — início"
            className="group flex items-center gap-3 focus-visible:rounded-md focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-amber-300"
            href="/"
          >
            <span className="grid size-9 place-items-center rounded-xl border border-amber-200/20 bg-amber-300/10 font-serif text-lg text-amber-100 transition group-hover:border-amber-200/35">
              M
            </span>
            <span className="text-sm font-semibold tracking-[0.16em] text-zinc-100 uppercase">
              Matinê
            </span>
          </Link>

          <nav aria-label="Navegação principal" className="hidden items-center gap-8 sm:flex">
            <a
              className="text-sm text-zinc-400 transition hover:text-zinc-100 focus-visible:rounded-sm focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-amber-300"
              href="#foundation"
            >
              Fundação
            </a>
            <a
              className="text-sm text-zinc-400 transition hover:text-zinc-100 focus-visible:rounded-sm focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-amber-300"
              href="#privacy"
            >
              Privacidade
            </a>
            <Badge tone="accent">Fase 1</Badge>
          </nav>

          <Badge className="sm:hidden" tone="accent">
            Fase 1
          </Badge>
        </div>
      </header>

      <main id="main-content">
        <section className="cinema-grid relative border-b border-white/[0.07]">
          <div className="ambient-glow absolute top-[-16rem] left-1/2 h-[32rem] w-[52rem] -translate-x-1/2 rounded-full bg-amber-500/[0.08] blur-[120px]" />
          <div className="relative mx-auto grid max-w-7xl items-center gap-14 px-5 py-20 sm:px-8 sm:py-28 lg:grid-cols-[1.02fr_0.98fr] lg:px-10 lg:py-32">
            <div className="max-w-2xl">
              <Badge tone="accent">Track · Discover · Together</Badge>
              <h1 className="mt-7 max-w-[13ch] text-balance font-serif text-5xl leading-[0.94] tracking-[-0.045em] text-white sm:text-7xl lg:text-[5.35rem]">
                O filme certo para este momento.
              </h1>
              <p className="mt-7 max-w-xl text-pretty text-base leading-7 text-zinc-400 sm:text-lg sm:leading-8">
                Uma casa para sua vida cinematográfica — e um jeito melhor de decidir o que assistir agora, sozinho ou junto de quem importa.
              </p>

              <div className="mt-9 flex flex-col gap-3 sm:flex-row">
                <a
                  className={buttonClassName("primary")}
                  href="#foundation"
                >
                  Conheça a fundação
                  <ArrowIcon />
                </a>
                <Link className={buttonClassName("secondary")} href="/search">
                  Explorar catálogo
                  <ArrowIcon />
                </Link>
              </div>

              <div className="mt-10 flex flex-wrap gap-x-6 gap-y-3 text-xs text-zinc-500">
                {[
                  "Privado por padrão",
                  "Sem tracking escondido",
                  "Recomendações explicáveis",
                ].map((item) => (
                  <span className="flex items-center gap-2" key={item}>
                    <span className="text-amber-300/80">
                      <CheckIcon />
                    </span>
                    {item}
                  </span>
                ))}
              </div>
            </div>

            <FilmFrames />
          </div>
        </section>

        <section
          className="mx-auto max-w-7xl px-5 py-20 sm:px-8 sm:py-28 lg:px-10"
          id="foundation"
        >
          <div className="grid gap-8 lg:grid-cols-[0.72fr_1.28fr] lg:gap-16">
            <div>
              <Badge>Base do produto</Badge>
              <h2 className="mt-6 max-w-[10ch] text-balance font-serif text-4xl leading-tight tracking-[-0.03em] text-white sm:text-5xl">
                Muito além de um catálogo.
              </h2>
              <p className="mt-5 max-w-md text-sm leading-7 text-zinc-500">
                A fundação segura está ativa e a busca pública do catálogo já está disponível. Biblioteca pessoal e recursos sociais continuam privados e entram somente após a base de autorização.
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              {foundationPillars.map((pillar) => (
                <Card className="group min-h-64 transition duration-300 hover:-translate-y-1 hover:border-white/[0.16]" key={pillar.id}>
                  <CardHeader>
                    <p className="font-mono text-[0.62rem] tracking-[0.2em] text-amber-200/60 uppercase">
                      {pillar.eyebrow}
                    </p>
                    <h3 className="text-balance text-xl font-semibold tracking-[-0.02em] text-zinc-100">
                      {pillar.title}
                    </h3>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm leading-6 text-zinc-500">{pillar.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        <section className="border-y border-white/[0.07] bg-white/[0.018]" id="privacy">
          <div className="mx-auto max-w-7xl px-5 py-20 sm:px-8 sm:py-24 lg:px-10">
            <div className="flex flex-col justify-between gap-6 border-b border-white/[0.08] pb-10 md:flex-row md:items-end">
              <div>
                <Badge tone="accent">Privacy by design</Badge>
                <h2 className="mt-6 max-w-2xl text-balance font-serif text-4xl leading-tight tracking-[-0.03em] text-white sm:text-5xl">
                  Seu gosto conta uma história. Ela continua sendo sua.
                </h2>
              </div>
              <p className="max-w-sm text-sm leading-7 text-zinc-500">
                Segurança e privacidade são decisões de arquitetura desde o primeiro commit, não ajustes para depois.
              </p>
            </div>

            <div className="grid gap-px pt-10 md:grid-cols-3">
              {privacyPrinciples.map((principle, index) => (
                <article
                  className="border-white/[0.08] py-7 md:border-l md:px-8 md:first:border-l-0 md:first:pl-0"
                  key={principle.id}
                >
                  <span className="font-mono text-[0.6rem] tracking-[0.22em] text-zinc-600 uppercase">
                    0{index + 1}
                  </span>
                  <h3 className="mt-4 text-lg font-semibold text-zinc-100">
                    {principle.title}
                  </h3>
                  <p className="mt-3 max-w-xs text-sm leading-6 text-zinc-500">
                    {principle.description}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-10 text-xs text-zinc-600 sm:flex-row sm:items-center sm:justify-between sm:px-8 lg:px-10">
        <p>Matinê · Fundação técnica + catálogo</p>
        <p>Fase 1 — nenhuma conta ou dado pessoal é coletado.</p>
      </footer>
    </div>
  );
}
