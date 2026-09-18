import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Matinê",
    short_name: "Matinê",
    description: "Seu cinema pessoal, privado por padrão.",
    start_url: "/",
    display: "standalone",
    background_color: "#08090b",
    theme_color: "#08090b",
    lang: "pt-BR",
    icons: [
      {
        src: "/icon.svg",
        sizes: "any",
        type: "image/svg+xml",
        purpose: "any maskable",
      },
    ],
  };
}
