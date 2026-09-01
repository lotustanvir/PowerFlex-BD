import type { Metadata } from "next";
import DashboardView from "./DashboardView";

export const metadata: Metadata = {
  title: "Live Dashboard — PowerFlex BD",
  description:
    "Real-time Bangladesh power grid monitoring dashboard with AI-driven solar forecasting, wind analysis, LoadShield optimization, and 9-zone renewable energy assessment.",
  alternates: { canonical: "/dashboard" },
};

export default function DashboardPage() {
  return <DashboardView />;
}
