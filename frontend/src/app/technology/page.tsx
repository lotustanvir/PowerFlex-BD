import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "PowerFlex BD Technology — AI, Grid Analytics & Renewable Optimization",
  description:
    "Explore the technology behind PowerFlex BD: XGBoost demand forecasting, solar AI prediction, wind power curve analysis, LoadShield multi-resource optimization, and real-time PGCB grid integration for Bangladesh.",
  keywords: [
    "AI energy optimization Bangladesh",
    "XGBoost demand forecasting",
    "solar AI prediction",
    "wind power curve",
    "PGCB grid integration",
    "LoadShield optimization",
  ],
  alternates: { canonical: "/technology" },
};

export default function TechnologyPage() {
  return (
    <main className="min-h-screen bg-gray-950 text-gray-100">
      <header className="border-b border-gray-800 bg-gray-900/60">
        <div className="mx-auto max-w-5xl px-6 py-16 text-center">
          <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl">
            Technology
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-gray-400">
            The AI-driven platform powering Bangladesh's energy transition — from
            real-time grid monitoring to renewable forecasting and multi-resource
            optimization.
          </p>
        </div>
      </header>

      <div className="mx-auto max-w-5xl space-y-20 px-6 py-20">
        {/* Grid Integration */}
        <section aria-labelledby="grid-integration">
          <article>
            <h2
              id="grid-integration"
              className="text-2xl font-semibold text-white"
            >
              Grid Integration
            </h2>
            <div className="mt-4 space-y-4 text-gray-300 leading-relaxed">
              <p>
                PowerFlex BD connects directly to the Bangladesh Power Grid
                Company (PGCB) data infrastructure through intelligent web
                scraping pipelines. Every fifteen minutes the platform ingests
                live generation, demand, frequency and interconnection data from
                the national dispatch centre.
              </p>
              <p>
                A dedicated ETL layer normalises the scraped ERP payloads,
                validates time-series continuity and stores the cleansed records
                in a time-series optimised database. Downstream services
                subscribe to the stream so that dashboards, forecast engines and
                the LoadShield optimizer always operate on fresh, authoritative
                grid state.
              </p>
              <p>
                All scraped data is cached locally with versioned snapshots,
                enabling historical replay for model training and post-event
                analysis even when the upstream source is temporarily
                unavailable.
              </p>
            </div>
          </article>
        </section>

        {/* Solar AI */}
        <section aria-labelledby="solar-ai">
          <article>
            <h2 id="solar-ai" className="text-2xl font-semibold text-white">
              Solar AI
            </h2>
            <div className="mt-4 space-y-4 text-gray-300 leading-relaxed">
              <p>
                The solar forecasting engine combines Open-Meteo&rsquo;s
                open-source weather API with a custom machine-learning model
                trained on Bangladesh-specific irradiance profiles. GHI, DHI and
                DNI values are requested for every hour of the coming seven-day
                horizon.
              </p>
              <p>
                To capture the country&rsquo;s significant intra-regional
                variability, Bangladesh is partitioned into nine geographical
                zones — Rangpur, Rajshahi, Mymensingh, Sylhet, Dhaka, Khulna,
                Barishal, Chattogram and the Hill Tracts. Each zone maintains its
                own model weights, trained on historical satellite-derived
                irradiance and ground-station measurements.
              </p>
              <p>
                The ML pipeline applies gradient-boosted regression on features
                including solar zenith angle, cloud cover fraction, aerosol
                optical depth and humidity. Predictions are output as both
                point-estimates and probabilistic intervals, allowing downstream
                systems to assess confidence before committing dispatch
                decisions.
              </p>
            </div>
          </article>
        </section>

        {/* Wind AI */}
        <section aria-labelledby="wind-ai">
          <article>
            <h2 id="wind-ai" className="text-2xl font-semibold text-white">
              Wind AI
            </h2>
            <div className="mt-4 space-y-4 text-gray-300 leading-relaxed">
              <p>
                Wind power estimation in Bangladesh relies on characterising the
                wind resource at hub height rather than surface level. The
                platform ingests 100-metre wind speed and direction data from
                Open-Meteo&rsquo;s reanalysis datasets, providing a physically
                meaningful input for turbine-level modelling.
              </p>
              <p>
                A library of manufacturer-provided power curves — covering
                Vestas, Siemens Gamesa and Goldwind turbines commonly deployed
                in South Asian coastal sites — is interpolated to estimate the
                electrical output for any given wind speed bin. Turbulence
                intensity and air-density corrections are applied to refine the
                estimate under Bangladesh&rsquo;s humid tropical conditions.
              </p>
              <p>
                The Wind AI module also flags periods of cut-in and cut-out
                risk, producing alerts that the LoadShield optimizer can use to
                pre-position conventional reserve before a predicted lull
                materialises.
              </p>
            </div>
          </article>
        </section>

        {/* LoadShield */}
        <section aria-labelledby="loadshield">
          <article>
            <h2 id="loadshield" className="text-2xl font-semibold text-white">
              LoadShield
            </h2>
            <div className="mt-4 space-y-4 text-gray-300 leading-relaxed">
              <p>
                LoadShield is the platform&rsquo;s multi-resource deficit
                optimizer. When projected demand exceeds available generation —
                whether due to seasonal peaks, fuel shortages or renewable
                intermittency — LoadShield determines the most cost-effective
                combination of actions to close the gap.
              </p>
              <p>
                The optimizer evaluates nine distinct resource categories:
                conventional thermal, combined-cycle gas, hydro import, solar
                curtailment release, wind dispatch, demand-response
                mobilisation, cross-border interchange, battery storage
                discharge and emergency diesel. Each category carries its own
                marginal cost, ramp-rate constraint and availability
                probability.
              </p>
              <p>
                A zone-aware solver runs for every one of the nine
                geographical zones simultaneously, producing a unified dispatch
                schedule that respects both local transmission capacity and the
                national grid&rsquo;s frequency stability requirements. The
                output is a prioritised action list presented to operators in
                real time.
              </p>
            </div>
          </article>
        </section>

        {/* Demand Forecast */}
        <section aria-labelledby="demand-forecast">
          <article>
            <h2
              id="demand-forecast"
              className="text-2xl font-semibold text-white"
            >
              Demand Forecast
            </h2>
            <div className="mt-4 space-y-4 text-gray-300 leading-relaxed">
              <p>
                Accurate load forecasting is critical for grid stability. PowerFlex
                BD employs an XGBoost regression model trained on a hybrid
                dataset: synthetic demand profiles generated from published
                Bangladesh load research studies, augmented with real PGCB
                historical dispatch records as anchor points.
              </p>
              <p>
                Feature engineering captures hourly-of-day seasonality,
                day-of-week effects, public-holiday flags, Ramadan fasting
                adjustments, temperature and humidity projections, and industrial
                production indices sourced from the Bangladesh Bureau of
                Statistics.
              </p>
              <p>
                The model outputs 24-hour ahead and seven-day ahead demand
                curves at both national and zone level. Rolling back-testing on
                the past twelve months of PGCB data achieves a mean absolute
                percentage error consistently below four per cent, providing
                operators with a reliable basis for unit commitment and fuel
                procurement planning.
              </p>
            </div>
          </article>
        </section>

        {/* Biomass Calculator */}
        <section aria-labelledby="biomass-calculator">
          <article>
            <h2
              id="biomass-calculator"
              className="text-2xl font-semibold text-white"
            >
              Biomass Calculator
            </h2>
            <div className="mt-4 space-y-4 text-gray-300 leading-relaxed">
              <p>
                Bangladesh possesses substantial untapped biomass resources. The
                Biomass Calculator quantifies this potential by integrating data
                from three authoritative sources: the FAOSTAT agricultural
                production database, the Department of Livestock Services (DLS)
                census of animal populations, and the Bangladesh Bureau of
                Statistics (BBS) crop-residue survey.
              </p>
              <p>
                The calculator disaggregates estimates to the division level —
                Dhaka, Chattogram, Rajshahi, Khulna, Barishal, Sylhet,
                Rangpur and Mymensingh — allowing regional energy planners to
                identify the most promising feedstock corridors. Crop residues
                (rice straw, jute stick, sugarcane bagasse), livestock manure
                and agro-industrial by-products are each modelled with
                conversion-efficiency factors appropriate to Bangladesh&rsquo;s
                dominant boiler and gasifier technologies.
              </p>
              <p>
                Outputs include annual tonnage availability, theoretical
                electricity generation potential (MW), associated CO₂
                displacement and the geographic density of feedstock clusters
                relative to existing grid substations.
              </p>
            </div>
          </article>
        </section>

        {/* Waste Calculator */}
        <section aria-labelledby="waste-calculator">
          <article>
            <h2
              id="waste-calculator"
              className="text-2xl font-semibold text-white"
            >
              Waste Calculator
            </h2>
            <div className="mt-4 space-y-4 text-gray-300 leading-relaxed">
              <p>
                Urban Bangladesh generates over 23,000 tonnes of municipal solid
                waste daily, yet less than half is collected systematically. The
                Waste Calculator translates city-level waste statistics into
                energy-recovery projections, helping municipalities evaluate the
                feasibility of waste-to-energy projects.
              </p>
              <p>
                The tool ingests waste composition data (organic fraction,
                plastics, textiles, inert materials) from city corporation
                reports and applies calorific-value models to estimate the
                thermal and electrical energy recoverable through incineration,
                anaerobic digestion or refuse-derived fuel pathways.
              </p>
              <p>
                A project-tracking module allows users to register proposed or
                operational waste-to-energy sites, monitor throughput against
                design capacity, and compare actual energy output with the
                calculator&rsquo;s baseline estimates. This creates a feedback
                loop that improves prediction accuracy over time and supports
                data-driven decisions about future plant siting and technology
                selection.
              </p>
            </div>
          </article>
        </section>
      </div>
    </main>
  );
}
