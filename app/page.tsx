export default function HomePage() {
  return (
    <main className="shell">
      <section className="hero" aria-labelledby="title">
        <span className="eyebrow">MATINÊ</span>
        <h1 id="title">Seu cinema, do seu jeito.</h1>
        <p>
          A base do projeto está no ar. Em breve: watchlist, diário, onde assistir,
          círculos e Movie Night.
        </p>
        <div className="status" role="status">
          <span className="statusDot" aria-hidden="true" />
          Ambiente pronto para deploy
        </div>
      </section>
    </main>
  );
}
