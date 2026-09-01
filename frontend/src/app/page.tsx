import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "PowerFlex BD — AI-Powered Bangladesh Power Intelligence Platform",
  description:
    "PowerFlex BD provides real-time Bangladesh power grid intelligence with AI-driven solar forecasting, wind analysis, LoadShield deficit optimization, and comprehensive renewable energy zone analysis.",
  openGraph: {
    title: "PowerFlex BD — AI-Powered Bangladesh Power Intelligence Platform",
    description:
      "Real-time Bangladesh power grid intelligence with AI-driven forecasting and optimization.",
    url: "/",
  },
  twitter: {
    card: "summary_large_image",
    title: "PowerFlex BD — AI-Powered Bangladesh Power Intelligence Platform",
    description:
      "Real-time Bangladesh power grid intelligence with AI-driven forecasting and optimization.",
  },
  alternates: { canonical: "/" },
};

export default function Home() {
  return (
    <>
      <header className="flex flex-col items-center justify-center py-20 text-center">
        <h1 className="text-5xl font-extrabold tracking-tight text-emerald-400">
          PowerFlex BD
        </h1>
        <p className="mt-4 max-w-2xl text-lg text-slate-300">
          AI-powered Bangladesh power intelligence — real-time grid monitoring,
          solar and wind forecasting, and load deficit optimization.
        </p>
      </header>

      <section aria-labelledby="features-heading" className="py-16">
        <h2
          id="features-heading"
          className="mb-10 text-center text-3xl font-bold"
        >
          Platform Features
        </h2>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <article className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <h3 className="mb-2 text-xl font-semibold text-emerald-400">
              Grid Monitoring
            </h3>
            <p className="text-sm text-slate-400">
              Real-time visibility into Bangladesh&apos;s 9 power grid zones
              with live demand, supply, and deficit data.
            </p>
          </article>

          <article className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <h3 className="mb-2 text-xl font-semibold text-emerald-400">
              Solar AI
            </h3>
            <p className="text-sm text-slate-400">
              AI-driven solar irradiance and generation forecasting using
              Open-Meteo data and proprietary models.
            </p>
          </article>

          <article className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <h3 className="mb-2 text-xl font-semibold text-emerald-400">
              Wind AI
            </h3>
            <p className="text-sm text-slate-400">
              Advanced wind speed and capacity factor predictions across all
              Bangladesh zones with seasonal analysis.
            </p>
          </article>

          <article className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <h3 className="mb-2 text-xl font-semibold text-emerald-400">
              LoadShield
            </h3>
            <p className="text-sm text-slate-400">
              Intelligent load-shedding deficit optimization that balances
              supply, demand, and renewable injection.
            </p>
          </article>
        </div>
      </section>

      <section aria-labelledby="stats-heading" className="py-16 text-center">
        <h2 id="stats-heading" className="mb-8 text-3xl font-bold">
          Comprehensive Coverage
        </h2>
        <div className="mx-auto grid max-w-3xl gap-8 sm:grid-cols-2">
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8">
            <span className="block text-4xl font-extrabold text-emerald-400">
              9
            </span>
            <span className="mt-2 block text-sm text-slate-400">
              Power Grid Zones
            </span>
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8">
            <span className="block text-4xl font-extrabold text-emerald-400">
              9
            </span>
            <span className="mt-2 block text-sm text-slate-400">
              Resource Types Tracked
            </span>
          </div>
        </div>
      </section>

      <section className="flex justify-center py-16">
        <a
          href="/dashboard"
          className="rounded-full bg-emerald-500 px-8 py-3 text-lg font-semibold text-slate-950 transition-colors hover:bg-emerald-400"
        >
          Open Dashboard
        </a>
      </section>
    </>
  );
}
