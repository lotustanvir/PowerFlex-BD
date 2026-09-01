import type { Metadata } from "next";
import HistoryView from "./HistoryView";

export const metadata: Metadata = {
  title: "Historical Data — PowerFlex BD",
  description:
    "Browse historical grid snapshots, AI predictions, LoadShield dispatches, and ML model registry for Bangladesh power grid.",
  alternates: { canonical: "/history" },
};

export default function HistoryPage() {
  return <HistoryView />;
}
