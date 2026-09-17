import { handleCatalogRequest } from "@/lib/tmdb.server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ segments?: string[] }> },
): Promise<Response> {
  const { segments = [] } = await params;
  return handleCatalogRequest(request, segments);
}
