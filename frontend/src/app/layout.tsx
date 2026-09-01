import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "PowerFlex BD — AI-Powered Bangladesh Power Intelligence Platform",
    template: "%s | PowerFlex BD",
  },
  description:
    "PowerFlex BD is an AI-powered Bangladesh power intelligence platform providing real-time grid data, solar and wind forecasting, LoadShield deficit optimization, and renewable energy zone analysis for the Bangladesh electricity sector.",
  keywords: [
    "Bangladesh power grid",
    "Bangladesh electricity",
    "Bangladesh power deficit",
    "Bangladesh load shedding",
    "Bangladesh renewable energy",
    "AI energy optimization Bangladesh",
    "PGCB electricity data",
    "solar forecast Bangladesh",
    "wind forecast Bangladesh",
    "biomass energy Bangladesh",
    "waste to energy Bangladesh",
    "energy intelligence Bangladesh",
  ],
  authors: [{ name: "PowerFlex BD" }],
  creator: "PowerFlex BD",
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL || "https://powerflexbd.com"
  ),
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "/",
    siteName: "PowerFlex BD",
    title: "PowerFlex BD — AI-Powered Bangladesh Power Intelligence Platform",
    description:
      "Real-time Bangladesh power grid intelligence with AI-driven solar forecasting, wind analysis, LoadShield optimization, and 9-zone renewable energy assessment.",
  },
  twitter: {
    card: "summary_large_image",
    title: "PowerFlex BD — AI-Powered Bangladesh Power Intelligence Platform",
    description:
      "Real-time Bangladesh power grid intelligence with AI-driven solar forecasting, wind analysis, and LoadShield optimization.",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  alternates: {
    canonical: "/",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    name: "PowerFlex BD",
    applicationCategory: "UtilityApplication",
    operatingSystem: "Web",
    description:
      "AI-powered Bangladesh power intelligence platform providing real-time grid monitoring, solar and wind forecasting, and renewable energy optimization.",
    url:
      process.env.NEXT_PUBLIC_SITE_URL || "https://powerflexbd.com",
    offers: {
      "@type": "Offer",
      price: "0",
      priceCurrency: "USD",
    },
    creator: {
      "@type": "Organization",
      name: "PowerFlex BD",
      description:
        "Independent AI energy intelligence platform for Bangladesh",
    },
  };

  return (
    <html lang="en" className="dark">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify(jsonLd),
          }}
        />
      </head>
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased">
        <nav aria-label="Main navigation" className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
          <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between px-4 py-3">
            <Link href="/" className="text-xl font-bold text-emerald-400">
              ⚡ PowerFlex BD
            </Link>
            <div className="flex flex-col gap-4 text-sm md:flex-row md:items-center md:gap-6">
              <Link href="/dashboard" className="hover:text-emerald-400">
                Dashboard
              </Link>
              <Link href="/solar" className="hover:text-emerald-400">
                Solar AI
              </Link>
              <Link href="/wind" className="hover:text-emerald-400">
                Wind AI
              </Link>
              <Link href="/loadshield" className="hover:text-emerald-400">
                LoadShield
              </Link>
              <Link href="/zones" className="hover:text-emerald-400">
                9 Zones
              </Link>
              <Link href="/resources" className="hover:text-emerald-400">
                Resources
              </Link>
              <Link href="/technology" className="hover:text-emerald-400">
                Technology
              </Link>
              <Link href="/about" className="hover:text-emerald-400">
                About
              </Link>
            </div>
          </div>
        </nav>
        <main className="mx-auto max-w-7xl px-4 py-6">
          {children}
        </main>
        <footer className="border-t border-slate-800 bg-slate-950 py-8 text-center text-sm text-slate-500">
          <p>
            PowerFlex BD — Independent AI Energy Intelligence Platform
            for Bangladesh
          </p>
          <p className="mt-2">
            Data sources: PGCB ERP, Open-Meteo, FAOSTAT, BBS, SREDA
          </p>
        </footer>
      </body>
    </html>
  );
}
