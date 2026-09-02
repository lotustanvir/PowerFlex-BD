import type { Metadata } from "next";
import DashboardView from "./DashboardView";

export const metadata: Metadata = {
  title: "Dashboard — PowerFlex BD",
  description:
    "Bangladesh power grid data, weather-driven solar and wind forecasts, demand forecasting, LoadShield scenario optimization, and 9-zone renewable energy assessment.",
  alternates: { canonical: "/dashboard" },
};

export default function DashboardPage() {
  return <DashboardView />;
}
