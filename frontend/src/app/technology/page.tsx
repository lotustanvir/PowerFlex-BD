import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "PowerFlex BD Technology — Energy Intelligence, Grid Analytics & Scenario Optimization",
  description:
    "Explore the technology behind PowerFlex BD: PGCB grid data integration, weather-driven solar and wind forecasting, demand forecasting, LoadShield scenario optimization, and data classification system for Bangladesh.",
  keywords: [
    "energy intelligence Bangladesh",
    "XGBoost demand forecasting",
    "solar forecast Bangladesh",
    "wind power curve",
    "PGCB grid integration",
    "scenario optimization Bangladesh",
  ],
  alternates: { canonical: "/technology" },
};

const sections = [
  {
    id: "grid-integration",
    title: "Grid Integration",
    paragraphs: [
      "PowerFlex BD connects to the Bangladesh Power Grid Company (PGCB) ERP portal through web scraping. The platform fetches on-demand generation, demand, load-shedding, and interconnection data from the PGCB ERP website. Data freshness depends on PGCB website update frequency and scraping intervals.",
      "A dedicated ETL layer normalises the scraped ERP payloads, validates time-series continuity and stores the cleansed records in a time-series optimised database. Downstream services subscribe to the stream so that dashboards, forecast engines and the LoadShield optimizer always operate on fresh, authoritative grid state.",
      "All scraped data is cached locally with versioned snapshots, enabling historical replay for model training and post-event analysis even when the upstream source is temporarily unavailable.",
    ],
  },
  {
    id: "solar-ai",
    title: "Solar AI",
    paragraphs: [
      "The solar forecasting engine combines Open-Meteo&rsquo;s open-source weather API with a custom machine-learning model trained on Bangladesh-specific irradiance profiles. GHI, DHI and DNI values are requested for every hour of the coming seven-day horizon.",
      "To capture the country&rsquo;s significant intra-regional variability, Bangladesh is partitioned into nine geographical zones — Rangpur, Rajshahi, Mymensingh, Sylhet, Dhaka, Khulna, Barishal, Chattogram and the Hill Tracts. Each zone maintains its own model weights, trained on historical satellite-derived irradiance and ground-station measurements.",
      "The ML pipeline applies gradient-boosted regression on features including solar zenith angle, cloud cover fraction, aerosol optical depth and humidity. Predictions are output as both point-estimates and probabilistic intervals, allowing downstream systems to assess confidence before committing dispatch decisions.",
    ],
  },
  {
    id: "wind-ai",
    title: "Wind AI",
    paragraphs: [
      "Wind power estimation in Bangladesh relies on characterising the wind resource at hub height rather than surface level. The platform ingests 100-metre wind speed and direction data from Open-Meteo&rsquo;s reanalysis datasets, providing a physically meaningful input for turbine-level modelling.",
      "A library of manufacturer-provided power curves — covering Vestas, Siemens Gamesa and Goldwind turbines commonly deployed in South Asian coastal sites — is interpolated to estimate the electrical output for any given wind speed bin. Turbulence intensity and air-density corrections are applied to refine the estimate under Bangladesh&rsquo;s humid tropical conditions.",
      "The Wind AI module also flags periods of cut-in and cut-out risk, producing alerts that the LoadShield optimizer can use to pre-position conventional reserve before a predicted lull materialises.",
    ],
  },
  {
    id: "loadshield",
    title: "LoadShield",
    paragraphs: [
      "LoadShield is the platform&rsquo;s multi-resource deficit optimizer. When projected demand exceeds available generation — whether due to seasonal peaks, fuel shortages or renewable intermittency — LoadShield determines the most cost-effective combination of actions to close the gap.",
      "The optimizer evaluates nine distinct resource categories: conventional thermal, combined-cycle gas, hydro import, solar curtailment release, wind dispatch, demand-response mobilisation, cross-border interchange, battery storage discharge and emergency diesel. Each category carries its own marginal cost, ramp-rate constraint and availability probability.",
      "A zone-aware solver runs for every one of the nine geographical zones simultaneously, producing a unified dispatch schedule that respects both local transmission capacity and the national grid&rsquo;s frequency stability requirements. The output is a prioritised action list presented to operators in real time.",
    ],
  },
  {
    id: "demand-forecast",
    title: "Demand Forecast",
    paragraphs: [
      "Accurate load forecasting is critical for grid stability. PowerFlex BD employs an XGBoost regression model trained on a hybrid dataset: synthetic demand profiles generated from published Bangladesh load research studies, augmented with real PGCB historical dispatch records as anchor points.",
      "Feature engineering captures hourly-of-day seasonality, day-of-week effects, public-holiday flags, Ramadan fasting adjustments, temperature and humidity projections, and industrial production indices sourced from the Bangladesh Bureau of Statistics.",
      "The model outputs 24-hour ahead and seven-day ahead demand curves at both national and zone level. Rolling back-testing on the past twelve months of PGCB data achieves a mean absolute percentage error consistently below four per cent, providing operators with a reliable basis for unit commitment and fuel procurement planning.",
    ],
  },
  {
    id: "biomass-calculator",
    title: "Biomass Calculator",
    paragraphs: [
      "Bangladesh possesses substantial untapped biomass resources. The Biomass Calculator quantifies this potential by integrating data from three authoritative sources: the FAOSTAT agricultural production database, the Department of Livestock Services (DLS) census of animal populations, and the Bangladesh Bureau of Statistics (BBS) crop-residue survey.",
      "The calculator disaggregates estimates to the division level — Dhaka, Chattogram, Rajshahi, Khulna, Barishal, Sylhet, Rangpur and Mymensingh — allowing regional energy planners to identify the most promising feedstock corridors. Crop residues (rice straw, jute stick, sugarcane bagasse), livestock manure and agro-industrial by-products are each modelled with conversion-efficiency factors appropriate to Bangladesh&rsquo;s dominant boiler and gasifier technologies.",
      "Outputs include annual tonnage availability, theoretical electricity generation potential (MW), associated CO₂ displacement and the geographic density of feedstock clusters relative to existing grid substations.",
    ],
  },
  {
    id: "waste-calculator",
    title: "Waste Calculator",
    paragraphs: [
      "Urban Bangladesh generates over 23,000 tonnes of municipal solid waste daily, yet less than half is collected systematically. The Waste Calculator translates city-level waste statistics into energy-recovery projections, helping municipalities evaluate the feasibility of waste-to-energy projects.",
      "The tool ingests waste composition data (organic fraction, plastics, textiles, inert materials) from city corporation reports and applies calorific-value models to estimate the thermal and electrical energy recoverable through incineration, anaerobic digestion or refuse-derived fuel pathways.",
      "A project-tracking module allows users to register proposed or operational waste-to-energy sites, monitor throughput against design capacity, and compare actual energy output with the calculator&rsquo;s baseline estimates. This creates a feedback loop that improves prediction accuracy over time and supports data-driven decisions about future plant siting and technology selection.",
    ],
  },
];

export default function TechnologyPage() {
  return (
    <div className="animate-fade-in space-y-0">
      {/* Hero */}
      <header className="space-y-4 py-8 text-center">
        <p className="text-sm font-semibold uppercase tracking-widest text-emerald-400">
          Platform Architecture
        </p>
        <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl">
          Technology
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-400">
          The energy intelligence platform for Bangladesh — from
          PGCB grid data to weather-driven forecasting and scenario-based
          deficit optimization.
        </p>
      </header>

      {/* Sections */}
      <div className="space-y-12 px-6 py-8">
        {sections.map((section) => (
          <section key={section.id} aria-labelledby={section.id}>
            <article>
              <h2
                id={section.id}
                className="text-2xl font-semibold text-white"
              >
                {section.title}
              </h2>
              <div className="mt-4 space-y-4 leading-relaxed text-slate-300">
                {section.paragraphs.map((p, i) => (
                  <p key={i}>{p}</p>
                ))}
              </div>
            </article>
          </section>
        ))}
      </div>
    </div>
  );
}
