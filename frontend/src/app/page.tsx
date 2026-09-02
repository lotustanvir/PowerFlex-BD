import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "PowerFlex BD — Energy Intelligence & Decision-Support Platform for Bangladesh",
  description:
    "PowerFlex BD is an independent energy intelligence platform for Bangladesh providing PGCB grid data, weather-driven solar and wind forecasts, calculated resource estimates, and scenario-based deficit optimization.",
  openGraph: {
    title: "PowerFlex BD — Energy Intelligence & Decision-Support Platform for Bangladesh",
    description:
      "Independent energy intelligence platform for Bangladesh with PGCB grid data, solar and wind forecasts, and scenario-based optimization.",
    url: "/",
  },
  twitter: {
    card: "summary_large_image",
    title: "PowerFlex BD — Energy Intelligence & Decision-Support Platform for Bangladesh",
    description:
      "Independent energy intelligence platform for Bangladesh with PGCB grid data, solar and wind forecasts, and scenario-based optimization.",
  },
  alternates: { canonical: "/" },
};

export default function Home() {
  return (
    <>
      <header className="flex flex-col items-center justify-center py-12 text-center">
        <h1 className="text-4xl font-extrabold tracking-tight text-emerald-400 sm:text-5xl">
          PowerFlex BD v2.0
        </h1>
        <p className="mt-3 max-w-2xl text-lg text-slate-300">
          Independent Energy Intelligence & Decision-Support Platform for Bangladesh.
          PGCB grid data, weather-driven forecasts, calculated resource estimates,
          and scenario-based deficit optimization.
        </p>
        <p className="mt-2 max-w-xl text-sm text-slate-500">
          This platform does NOT operate, control, or issue dispatch commands
          to the Bangladesh national grid.
        </p>
        <div className="mt-6 flex items-center gap-3">
          <a
            href="/dashboard"
            className="rounded-lg bg-emerald-500 px-6 py-2.5 text-sm font-semibold text-slate-950 transition-colors hover:bg-emerald-400"
          >
            Open Dashboard
          </a>
          <a
            href="/technology"
            className="rounded-lg border border-slate-700 px-6 py-2.5 text-sm font-medium text-slate-300 transition-colors hover:border-slate-500 hover:text-white"
          >
            Technology
          </a>
        </div>
      </header>

      <section aria-labelledby="features-heading" className="py-10">
        <h2
          id="features-heading"
          className="mb-6 text-center text-2xl font-bold"
        >
          Platform Features
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <a href="/dashboard" className="group rounded-xl border border-slate-800 bg-slate-900/60 p-5 transition-colors hover:border-slate-700 hover:bg-slate-800/60">
            <h3 className="mb-1.5 text-lg font-semibold text-emerald-400 group-hover:text-emerald-300">
              Grid Data
            </h3>
            <p className="text-sm text-slate-400">
              Official PGCB ERP demand, supply, load-shedding, and generation
              breakdown data with source attribution.
            </p>
          </a>

          <a href="/solar" className="group rounded-xl border border-slate-800 bg-slate-900/60 p-5 transition-colors hover:border-slate-700 hover:bg-slate-800/60">
            <h3 className="mb-1.5 text-lg font-semibold text-emerald-400 group-hover:text-emerald-300">
              Solar Forecast
            </h3>
            <p className="text-sm text-slate-400">
              Weather-driven solar generation forecast using Open-Meteo data
              and XGBoost model. Experimental — not validated against real
              Bangladesh solar farm output.
            </p>
          </a>

          <a href="/wind" className="group rounded-xl border border-slate-800 bg-slate-900/60 p-5 transition-colors hover:border-slate-700 hover:bg-slate-800/60">
            <h3 className="mb-1.5 text-lg font-semibold text-emerald-400 group-hover:text-emerald-300">
              Wind Estimation
            </h3>
            <p className="text-sm text-slate-400">
              Engineering power-curve model applied to 100m wind speed data.
              Experimental — not validated against real Bangladesh wind turbine
              telemetry.
            </p>
          </a>

          <a href="/loadshield" className="group rounded-xl border border-slate-800 bg-slate-900/60 p-5 transition-colors hover:border-slate-700 hover:bg-slate-800/60">
            <h3 className="mb-1.5 text-lg font-semibold text-emerald-400 group-hover:text-emerald-300">
              LoadShield
            </h3>
            <p className="text-sm text-slate-400">
              Scenario-based deficit optimization recommending resource
              deployment across 9 zones. Not a real-time grid dispatch system.
            </p>
          </a>
        </div>
      </section>

      <section aria-labelledby="disclaimer-heading" className="py-6">
        <div className="mx-auto max-w-4xl rounded-xl border border-amber-800/50 bg-amber-950/30 p-5">
          <h2 id="disclaimer-heading" className="mb-2 text-base font-semibold text-amber-400">
            Scientific Disclaimer
          </h2>
          <p className="text-sm text-slate-400 leading-relaxed">
            PowerFlex BD is an independent energy intelligence and
            decision-support platform. It does not operate, control, or
            issue dispatch commands to the Bangladesh national grid.
            Forecasts, calculated estimates, technical potential assessments,
            and scenario analyses presented on this platform must not be
            interpreted as official real-time grid measurements or as
            dispatch commands.
          </p>
        </div>
      </section>

      <section aria-labelledby="stats-heading" className="py-10 text-center">
        <h2 id="stats-heading" className="mb-6 text-2xl font-bold">
          Comprehensive Coverage
        </h2>
        <div className="mx-auto grid max-w-4xl gap-6 sm:grid-cols-3">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
            <span className="block text-3xl font-extrabold text-emerald-400">
              9
            </span>
            <span className="mt-1 block text-sm text-slate-400">
              Power Grid Zones
            </span>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
            <span className="block text-3xl font-extrabold text-emerald-400">
              9
            </span>
            <span className="mt-1 block text-sm text-slate-400">
              Resource Types
            </span>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
            <span className="block text-3xl font-extrabold text-emerald-400">
              6
            </span>
            <span className="mt-1 block text-sm text-slate-400">
              Data Classifications
            </span>
          </div>
        </div>
      </section>

      <section aria-labelledby="explore-heading" className="py-8">
        <h2 id="explore-heading" className="mb-4 text-center text-2xl font-bold">
          Explore the Platform
        </h2>
        <div className="mx-auto grid max-w-4xl gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {[
            { href: "/zones", label: "9-Zone Analysis", desc: "Renewable energy assessment across Bangladesh" },
            { href: "/resources", label: "Energy Resources", desc: "All 9 resource types and classifications" },
            { href: "/solar", label: "Solar AI", desc: "Weather-driven solar generation forecast" },
            { href: "/wind", label: "Wind AI", desc: "Engineering-based wind power estimation" },
            { href: "/loadshield", label: "LoadShield", desc: "Scenario-based deficit optimization" },
            { href: "/technology", label: "Technology", desc: "How the platform works" },
          ].map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 transition-colors hover:border-slate-700 hover:bg-slate-800/60"
            >
              <h3 className="text-sm font-semibold text-white">{item.label}</h3>
              <p className="mt-0.5 text-xs text-slate-400">{item.desc}</p>
            </a>
          ))}
        </div>
      </section>
    </>
  );
}
