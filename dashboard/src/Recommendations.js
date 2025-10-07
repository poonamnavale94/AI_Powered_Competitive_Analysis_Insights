import React from "react";

function Recommendations({ product, marketing }) {
  return (
    <div className="card">
      <h2>Recommendations</h2>

      <h3>Product</h3>
      <ul>
        {product.map((item, idx) => (
          <li key={idx}>{item}</li>
        ))}
      </ul>

      <h3>Marketing</h3>
      <ul>
        {marketing.campaign_themes.map((theme, idx) => (
          <li key={idx}>{theme}</li>
        ))}
      </ul>
    </div>
  );
}

export default Recommendations;
