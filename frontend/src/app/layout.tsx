import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "PowerFlex BD — Energy Intelligence & Decision-Support Platform for Bangladesh",
    template: "%s | PowerFlex BD",
  },
  description:
    "PowerFlex BD is an independent energy intelligence and decision-support platform for Bangladesh providing grid data from PGCB, weather-driven solar and wind forecasts, calculated resource estimates, demand forecasting, and scenario-based deficit optimization. This platform does NOT operate or control the Bangladesh national grid.",
  keywords: [
    "Bangladesh power grid",
    "Bangladesh electricity",
    "Bangladesh power deficit",
    "Bangladesh load shedding",
    "Bangladesh renewable energy",
    "energy intelligence Bangladesh",
    "PGCB electricity data",
    "solar forecast Bangladesh",
    "wind forecast Bangladesh",
    "biomass energy Bangladesh",
    "waste to energy Bangladesh",
    "energy decision support Bangladesh",
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
    title: "PowerFlex BD — Energy Intelligence & Decision-Support Platform for Bangladesh",
    description:
      "Independent energy intelligence platform for Bangladesh with PGCB grid data, weather-driven solar and wind forecasts, calculated resource estimates, and scenario-based deficit optimization.",
  },
  twitter: {
    card: "summary_large_image",
    title: "PowerFlex BD — Energy Intelligence & Decision-Support Platform for Bangladesh",
    description:
      "Independent energy intelligence platform for Bangladesh with PGCB grid data, solar and wind forecasts, and scenario-based optimization.",
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

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", short: "Dash" },
  { href: "/solar", label: "Solar AI", short: "Solar" },
  { href: "/wind", label: "Wind AI", short: "Wind" },
  { href: "/loadshield", label: "LoadShield", short: "LS" },
  { href: "/zones", label: "9 Zones", short: "Zones" },
  { href: "/resources", label: "Resources", short: "Res" },
  { href: "/history", label: "History", short: "Hist" },
  { href: "/technology", label: "Technology", short: "Tech" },
  { href: "/about", label: "About", short: "About" },
];

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
      "Independent energy intelligence and decision-support platform for Bangladesh providing PGCB grid data, weather-driven forecasts, calculated resource estimates, and scenario-based optimization.",
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
        "Independent energy intelligence and decision-support platform for Bangladesh. Does not operate or control the Bangladesh national grid.",
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
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>

        {/* Navigation */}
        <nav
          aria-label="Main navigation"
          className="sticky top-0 z-50 border-b border-slate-800/80 bg-slate-950/85 backdrop-blur-xl"
        >
          <div className="mx-auto flex max-w-screen-2xl items-center justify-between px-4 py-0 sm:px-6">
            {/* Brand */}
            <Link
              href="/"
              className="flex items-center gap-2 py-3 text-base font-bold tracking-tight text-emerald-400 transition-colors hover:text-emerald-300"
            >
              <span className="inline-flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500/15 text-sm">
                ⚡
              </span>
              <span>PowerFlex BD</span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden items-center gap-1 md:flex" role="menubar">
              {NAV_ITEMS.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  role="menuitem"
                  className="rounded-md px-3 py-2 text-[13px] font-medium text-slate-400 transition-colors hover:bg-slate-800/60 hover:text-white"
                >
                  {item.label}
                </Link>
              ))}
            </div>

            {/* Mobile hamburger (CSS-only toggle) */}
            <div className="md:hidden">
              <input
                type="checkbox"
                id="mobile-nav-toggle"
                className="peer hidden"
                aria-label="Toggle navigation menu"
              />
              <label
                htmlFor="mobile-nav-toggle"
                className="inline-flex cursor-pointer items-center justify-center rounded-md p-2 text-slate-400 transition-colors hover:bg-slate-800/60 hover:text-white"
                aria-hidden="true"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
                </svg>
              </label>
              {/* Mobile dropdown */}
              <div className="absolute left-0 right-0 top-full z-50 hidden border-b border-slate-800 bg-slate-950/95 p-3 backdrop-blur-xl peer-checked:block">
                <div className="flex flex-col gap-1">
                  {NAV_ITEMS.map((item) => (
                    <Link
                      key={item.href}
                      href={item.href}
                      className="rounded-md px-3 py-2.5 text-sm font-medium text-slate-400 transition-colors hover:bg-slate-800/60 hover:text-white"
                    >
                      {item.label}
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main id="main-content" className="mx-auto max-w-screen-2xl px-4 py-6 sm:px-6">
          {children}
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-800/60 bg-slate-950">
          <div className="mx-auto max-w-screen-2xl px-4 py-8 sm:px-6">
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {/* Brand */}
              <div>
                <p className="text-sm font-semibold text-white">⚡ PowerFlex BD</p>
                <p className="mt-2 text-xs leading-relaxed text-slate-500">
                  Independent energy intelligence &amp; decision-support platform for Bangladesh.
                </p>
              </div>

              {/* Data Sources */}
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Data Sources</p>
                <p className="mt-2 text-xs leading-relaxed text-slate-500">
                  PGCB ERP · Open-Meteo · FAOSTAT · BBS · SREDA
                </p>
              </div>

              {/* Platform */}
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Platform</p>
                <div className="mt-2 flex flex-col gap-1">
                  <Link href="/technology" className="text-xs text-slate-500 transition-colors hover:text-emerald-400">Technology</Link>
                  <Link href="/about" className="text-xs text-slate-500 transition-colors hover:text-emerald-400">About</Link>
                  <Link href="/resources" className="text-xs text-slate-500 transition-colors hover:text-emerald-400">Resources</Link>
                </div>
              </div>

              {/* Disclaimer */}
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Disclaimer</p>
                <p className="mt-2 text-[11px] leading-relaxed text-slate-600">
                  This platform does NOT operate, control, or issue dispatch commands to the Bangladesh national grid.
                  Forecasts must not be interpreted as official real-time grid measurements.
                </p>
              </div>
            </div>

            <div className="mt-6 border-t border-slate-800/40 pt-4 text-center text-[11px] text-slate-600">
              PowerFlex BD v2.0 · Independent Energy Intelligence · Not affiliated with PGCB
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
