import { useEffect, useState } from "react";

import ProjectionAlert from "./components/ProjectionAlert";
import Heatmap from "./components/Heatmap";
import WeekComparison from "./components/WeekComparison";
import Activities from "./components/Activities";
import StepsTrend from "./components/StepsTrend";
import StepStats from "./components/StepStats";
import Changelog from "./components/Changelog";
import Cheer from "./components/Cheer";
import Impressum from "./components/Impressum";
import Datenschutz from "./components/Datenschutz";

function scrollToSupport() {
  document.getElementById("support")?.scrollIntoView({ behavior: "smooth" });
}

// Hash-based routing (#/impressum, #/datenschutz) instead of a router lib:
// GitHub Pages serves only index.html, so path-based routes would 404 on
// reload without a fallback hack.
function useHashRoute() {
  const [hash, setHash] = useState(() => window.location.hash);

  useEffect(() => {
    const onHashChange = () => {
      setHash(window.location.hash);
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  return hash;
}

// Layout per specs/0005: one time horizon per row — alert (the guilt trip),
// heatmap (the year), this week, history. Nothing goes above the heatmap
// except the alert.
function Dashboard() {
  return (
    <>
      <div className="flex items-center justify-center gap-3">
        <h1 className="text-3xl font-bold text-blue-400 text-center">Wandern Eric</h1>
        <button
          onClick={scrollToSupport}
          className="cursor-pointer text-sm bg-blue-400 text-white font-semibold px-3 py-1 rounded-full"
        >
          👏 Support
        </button>
      </div>

      <div className="mx-auto mt-5 flex flex-col gap-5">
        <ProjectionAlert />

        <Heatmap />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 items-stretch">
          <div className="lg:col-span-2">
            <WeekComparison />
          </div>
          <Activities />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 items-stretch">
          <div className="lg:col-span-2">
            <StepsTrend />
          </div>
          <StepStats />
        </div>

        <Cheer />

        <Changelog />
      </div>
    </>
  );
}

const PAGES = {
  "#/impressum": Impressum,
  "#/datenschutz": Datenschutz,
};

export default function App() {
  const hash = useHashRoute();
  const Page = PAGES[hash];

  return (
    <div className="min-h-screen w-full bg-gray-100 p-6">
      {Page ? <Page /> : <Dashboard />}

      <footer className="mt-8 flex justify-center gap-3 text-sm text-gray-400">
        <a href="#/impressum" className="hover:text-blue-400">
          Impressum
        </a>
        <span>·</span>
        <a href="#/datenschutz" className="hover:text-blue-400">
          Datenschutz
        </a>
      </footer>
    </div>
  );
}
