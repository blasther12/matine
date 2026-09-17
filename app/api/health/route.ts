export function GET() {
  return Response.json(
    { status: "ok", service: "matine-web" },
    {
      headers: {
        "Cache-Control": "no-store",
      },
    },
  );
}
