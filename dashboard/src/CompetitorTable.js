import React from "react";

function CompetitorTable({ competitors }) {
  return (
    <div className="card">
      <h2>Competitor Insights</h2>
      <table>
        <thead>
          <tr>
            <th>Competitor</th>
            <th>Strengths</th>
            <th>Weaknesses</th>
          </tr>
        </thead>
        <tbody>
          {competitors.map((c, idx) => (
            <tr key={idx}>
              <td>{c.competitor}</td>
              <td>{c.strengths.join(", ")}</td>
              <td>{c.weaknesses.join(", ")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default CompetitorTable;
