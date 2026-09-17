export default function LibraryLoading() {
  return (
    <main className="min-h-screen bg-background px-5 py-20 text-foreground">
      <div className="mx-auto max-w-7xl animate-pulse">
        <div className="h-4 w-32 rounded bg-white/10" />
        <div className="mt-6 h-14 w-72 max-w-full rounded bg-white/10" />
        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }, (_, index) => <div className="aspect-[2/3] rounded-2xl bg-white/[0.06]" key={index} />)}
        </div>
      </div>
    </main>
  );
}
