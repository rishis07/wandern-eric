import ProjectionAlert from "./components/ProjectionAlert";
import Heatmap from "./components/Heatmap";
import WeekComparison from "./components/WeekComparison";
import Activities from "./components/Activities";
import StepsTrend from "./components/StepsTrend";
import StepStats from "./components/StepStats";
import Changelog from "./components/Changelog";
import Cheer from "./components/Cheer";

function scrollToSupport() {
  document.getElementById("support")?.scrollIntoView({ behavior: "smooth" });
}

// Layout per specs/0005: one time horizon per row — alert (the guilt trip),
// heatmap (the year), this week, history. Nothing goes above the heatmap
// except the alert.
export default function App() {
  return (
    <div className="min-h-screen w-full bg-gray-100 p-6">
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
    </div>
  );
}
