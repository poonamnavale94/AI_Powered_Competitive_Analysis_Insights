import React from "react";
import { Bar } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

function KeywordChart({ data }) {
  const labels = data.keywords || [];
  const counts = labels.map(() => Math.floor(Math.random() * 10 + 1)); // placeholder counts

  const chartData = {
    labels,
    datasets: [
      {
        label: "Keyword Frequency",
        data: counts,
        backgroundColor: "rgba(75, 192, 192, 0.6)",
      },
    ],
  };

  return (
    <div className="card">
      <h2>Keyword Insights</h2>
      <Bar data={chartData} />
    </div>
  );
}

export default KeywordChart;