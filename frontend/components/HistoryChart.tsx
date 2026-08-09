"use client";

import { useMemo, useState } from "react";
import { GovernmentPeriod, IndicatorValuePoint } from "@/lib/types";
import { formatNumber, formatDate } from "@/lib/format";

const WIDTH = 800;
const HEIGHT = 320;
const PADDING = { top: 16, right: 16, bottom: 28, left: 48 };

function firstName(fullName: string): string {
  return fullName.split(" ")[0];
}

export default function HistoryChart({
  history,
  unit,
  governmentPeriods,
}: {
  history: IndicatorValuePoint[];
  unit: string;
  governmentPeriods: GovernmentPeriod[];
}) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const chart = useMemo(() => {
    if (history.length < 2) return null;

    const times = history.map((p) => new Date(p.reference_date).getTime());
    const values = history.map((p) => p.value);
    const minTime = Math.min(...times);
    const maxTime = Math.max(...times);
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);
    const valuePadding = (maxValue - minValue) * 0.1 || 1;
    const yMin = minValue - valuePadding;
    const yMax = maxValue + valuePadding;

    const innerWidth = WIDTH - PADDING.left - PADDING.right;
    const innerHeight = HEIGHT - PADDING.top - PADDING.bottom;

    const x = (time: number) =>
      PADDING.left + ((time - minTime) / (maxTime - minTime || 1)) * innerWidth;
    const y = (value: number) =>
      PADDING.top + innerHeight - ((value - yMin) / (yMax - yMin || 1)) * innerHeight;

    const linePath = history
      .map((p, i) => `${i === 0 ? "M" : "L"} ${x(times[i]).toFixed(1)} ${y(p.value).toFixed(1)}`)
      .join(" ");

    const gridLines = [yMin, (yMin + yMax) / 2, yMax];

    const periodMarkers = governmentPeriods
      .filter((period) => {
        const start = new Date(period.start_date).getTime();
        return start > minTime && start < maxTime;
      })
      .map((period) => ({
        ...period,
        xPos: x(new Date(period.start_date).getTime()),
      }));

    return { times, x, y, linePath, gridLines, periodMarkers, innerHeight };
  }, [history, governmentPeriods]);

  if (!chart) {
    return <p className="text-sm text-gray-500">Histórico insuficiente para exibir gráfico.</p>;
  }

  const handleMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const svg = e.currentTarget;
    const rect = svg.getBoundingClientRect();
    const relativeX = ((e.clientX - rect.left) / rect.width) * WIDTH;
    let nearest = 0;
    let nearestDist = Infinity;
    chart.times.forEach((time, i) => {
      const dist = Math.abs(chart.x(time) - relativeX);
      if (dist < nearestDist) {
        nearestDist = dist;
        nearest = i;
      }
    });
    setHoverIndex(nearest);
  };

  const hovered = hoverIndex !== null ? history[hoverIndex] : history[history.length - 1];
  const hoveredX = hoverIndex !== null ? chart.x(chart.times[hoverIndex]) : chart.x(chart.times[chart.times.length - 1]);

  return (
    <div>
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        className="w-full h-auto"
        role="img"
        aria-label={`Gráfico histórico, de ${formatDate(history[0].reference_date)} a ${formatDate(
          history[history.length - 1].reference_date
        )}`}
        onMouseMove={handleMove}
        onMouseLeave={() => setHoverIndex(null)}
      >
        {chart.gridLines.map((value, i) => (
          <g key={i}>
            <line
              x1={PADDING.left}
              x2={WIDTH - PADDING.right}
              y1={chart.y(value)}
              y2={chart.y(value)}
              stroke="var(--color-gray-100)"
              strokeWidth={1}
            />
            <text x={4} y={chart.y(value) + 4} fontSize={11} fill="var(--color-gray-500)">
              {formatNumber(value, unit)}
            </text>
          </g>
        ))}

        {chart.periodMarkers.map((marker, i) => (
          <g key={i}>
            <line
              x1={marker.xPos}
              x2={marker.xPos}
              y1={PADDING.top}
              y2={PADDING.top + chart.innerHeight}
              stroke="var(--color-gray-100)"
              strokeWidth={1}
              strokeDasharray="2,3"
            />
            <text
              x={marker.xPos + 4}
              y={HEIGHT - 8}
              fontSize={9}
              fill="var(--color-gray-500)"
            >
              {firstName(marker.holder_name)}
            </text>
          </g>
        ))}

        <path d={chart.linePath} fill="none" stroke="var(--color-ink)" strokeWidth={1.5} />

        {hoverIndex !== null && (
          <line
            x1={hoveredX}
            x2={hoveredX}
            y1={PADDING.top}
            y2={PADDING.top + chart.innerHeight}
            stroke="var(--color-gray-500)"
            strokeWidth={1}
          />
        )}

        <circle
          cx={chart.x(chart.times[history.length - 1])}
          cy={chart.y(history[history.length - 1].value)}
          r={3.5}
          fill="var(--color-yellow)"
          stroke="var(--color-ink)"
          strokeWidth={1}
        />

        {hoverIndex !== null && (
          <circle cx={hoveredX} cy={chart.y(hovered.value)} r={3} fill="var(--color-ink)" />
        )}
      </svg>

      <div className="mt-1 text-sm text-gray-500 flex items-center justify-between">
        <span>{formatDate(history[0].reference_date)}</span>
        <span className="font-medium text-ink">
          {formatDate(hovered.reference_date)}: {formatNumber(hovered.value, unit)}
        </span>
        <span>{formatDate(history[history.length - 1].reference_date)}</span>
      </div>
    </div>
  );
}
