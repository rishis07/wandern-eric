import Heatmap from "./components/Heatmap";
import Aggregations from "./components/Aggregations";

export default function App() {
  return (
    <div className="min-h-screen w-full bg-gray-100 p-6">
      <h1 className="text-3xl font-bold text-blue-400 text-center">Wandern Eric</h1>

      <div className="mx-auto mt-5">
        <Heatmap />
      </div>

      <div className="mx-auto mt-5">
        <Aggregations />
      </div>
    </div>
  );
}