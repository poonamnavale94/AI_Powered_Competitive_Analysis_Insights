import { useEffect, useState, useRef } from "react";

function Dashboard() {
  const [insights, setInsights] = useState(null);
  const [openSections, setOpenSections] = useState({});

  useEffect(() => {
    fetch("https://ai-competitive-insights.herokuapp.com/api/insights")
      .then((res) => res.json())
      .then((data) => {
        if (data.length > 0 && data[0].insights_raw) {
          try {
            const parsed = JSON.parse(data[0].insights_raw);
            setInsights(parsed);
          } catch (err) {
            console.error("Error parsing cleaned insights JSON:", err);
          }
        }
      })
      .catch((err) => console.error("Error fetching insights:", err));
  }, []);

  if (!insights)
    return (
      <div className="p-6 text-center text-gray-500 text-lg animate-pulse">
        Loading insights...
      </div>
    );

  const toggleSection = (key) => {
    setOpenSections((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // 🎨 Unified card style
  const cardStyle =
    "bg-gradient-to-br from-white to-[#F3F7FF] shadow-lg rounded-2xl border border-[#E0E7FF] flex flex-col transform transition-all duration-300 hover:shadow-xl hover:-translate-y-1";

  // 🔢 Render numbered list instead of bullet points
  const renderNumberedList = (list) =>
    list?.length ? (
      <ol className="list-decimal list-inside space-y-1 text-gray-800 leading-relaxed">
        {list.map((item, i) => (
          <li key={i} className="pl-1">
            {item}
          </li>
        ))}
      </ol>
    ) : (
      <p className="text-gray-500">No data available</p>
    );

  // 🔽 Collapsible card component
  const Collapsible = ({ title, children, sectionKey }) => {
    const contentRef = useRef(null);
    const isOpen = openSections[sectionKey];
    const maxHeight = isOpen
      ? `${contentRef.current?.scrollHeight}px`
      : "0px";

    return (
      <section className={cardStyle}>
        <button
          className="flex justify-between items-center w-full text-left font-semibold text-[#4A90E2] text-lg md:text-xl px-5 py-4 hover:text-[#2E6FD0] transition-colors"
          onClick={() => toggleSection(sectionKey)}
        >
          <span>{title}</span>
          <span className="text-sm">{isOpen ? "▲" : "▼"}</span>
        </button>
        <div
          ref={contentRef}
          style={{ maxHeight }}
          className="overflow-hidden transition-all duration-700 px-5"
        >
          <div className="pb-5 mt-1">{children}</div>
        </div>
      </section>
    );
  };

  return (
    <div className="p-6 md:p-10 space-y-8 bg-[#F8FAFF] min-h-screen">
      <h1 className="text-3xl md:text-4xl font-bold text-[#4A90E2] mb-4 tracking-tight">
        Competitive Analysis Insights Dashboard
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {/* 🧭 Executive Summary */}
        <Collapsible title="Executive Summary" sectionKey="executive_summary">
          <p className="text-gray-700 leading-relaxed text-justify">
            {insights.executive_summary}
          </p>
        </Collapsible>

        {/* ⚔️ Competitor Insights */}
        <Collapsible title="Competitor Insights" sectionKey="competitor_insights">
          {insights.competitor_insights?.map((comp, idx) => (
            <div
              key={idx}
              className="p-3 border-b border-gray-200 last:border-b-0 rounded-md bg-white/60 backdrop-blur-sm"
            >
              <h3 className="font-semibold text-[#4A90E2] text-lg mb-2">
                {comp.competitor}
              </h3>
              <div className="flex flex-col gap-3 text-sm">
                <div>
                  <span className="font-medium text-gray-700 block">
                    Strengths
                  </span>
                  <ul className="flex flex-wrap gap-2 mt-1">
                    {comp.strengths.map((s, i) => (
                      <li
                        key={i}
                        className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full"
                      >
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <span className="font-medium text-gray-700 block">
                    Weaknesses
                  </span>
                  <ul className="flex flex-wrap gap-2 mt-1">
                    {comp.weaknesses.map((w, i) => (
                      <li
                        key={i}
                        className="bg-red-100 text-red-700 text-xs px-2 py-1 rounded-full"
                      >
                        {w}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </Collapsible>

        {/* 💡 Product Manager Recommendations */}
        <Collapsible
          title="Recommendations for Product Manager"
          sectionKey="product_manager"
        >
          {renderNumberedList(insights.recommendations_for_product_manager)}
        </Collapsible>

        {/* 📈 Marketing Team Recommendations */}
        <Collapsible
          title="Recommendations for Marketing Team"
          sectionKey="marketing_team"
        >
          {[
            "campaign_themes",
            "keywords",
            "Marketing_campaign",
            "pain_points",
            "market_gaps",
          ].map((key) => (
            <div
              key={key}
              className="mb-4 bg-white/70 rounded-lg p-3 shadow-sm hover:shadow-md transition-shadow"
            >
              <h3 className="font-semibold text-[#4A90E2] text-base mb-2">
                {key.replace(/_/g, " ").toUpperCase()}
              </h3>
              {renderNumberedList(
                insights.recommendations_for_marketing_team[key]
              )}
            </div>
          ))}
        </Collapsible>

        {/* ⚖️ Regulatory Notes */}
        <Collapsible title="Regulatory Notes" sectionKey="regulatory_notes">
          <table className="w-full text-sm border-collapse">
            <tbody>
              {Object.entries(insights.regulatory_notes || {}).map(([k, v]) => (
                <tr key={k} className="border-b last:border-b-0">
                  <td className="font-medium text-gray-700 py-2 pr-3">{k}</td>
                  <td className="text-gray-800">{v}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Collapsible>
      </div>
    </div>
  );
}

export default Dashboard;
