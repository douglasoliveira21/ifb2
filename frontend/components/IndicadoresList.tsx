"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { IndicatorSummary } from "@/lib/types";
import { formatNumber } from "@/lib/format";
import { CATEGORY_LABELS, CATEGORY_ORDER } from "@/lib/categories";
import ClassificationBadge from "@/components/ClassificationBadge";

function normalize(value: string): string {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "");
}

export default function IndicadoresList({ indicators }: { indicators: IndicatorSummary[] }) {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = normalize(query.trim());
    if (!q) return indicators;
    return indicators.filter(
      (i) => normalize(i.name).includes(q) || normalize(CATEGORY_LABELS[i.category] ?? i.category).includes(q)
    );
  }, [indicators, query]);

  const byCategory = useMemo(() => {
    const map = new Map<string, IndicatorSummary[]>();
    for (const indicator of filtered) {
      const list = map.get(indicator.category) ?? [];
      list.push(indicator);
      map.set(indicator.category, list);
    }
    return map;
  }, [filtered]);

  const categories = CATEGORY_ORDER.filter((c) => byCategory.has(c));

  return (
    <>
      <section className="mx-auto max-w-6xl px-4 sm:px-6 pb-6">
        <label htmlFor="busca-indicadores" className="sr-only">
          Buscar indicador
        </label>
        <input
          id="busca-indicadores"
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Buscar por nome do indicador ou categoria…"
          className="w-full border border-ink px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-ink"
        />
        {query && (
          <p className="mt-2 text-sm text-gray-500">
            {filtered.length === 0
              ? "Nenhum indicador encontrado."
              : `${filtered.length} indicador${filtered.length === 1 ? "" : "es"} encontrado${filtered.length === 1 ? "" : "s"}.`}
          </p>
        )}
      </section>

      {categories.map((category) => (
        <section key={category} className="border-t border-ink">
          <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8">
            <h2 className="text-xl font-bold uppercase tracking-wide">
              {CATEGORY_LABELS[category] ?? category}
            </h2>
            <ul className="mt-4 divide-y divide-gray-100">
              {byCategory.get(category)!.map((indicator) => (
                <li key={indicator.indicator_id}>
                  <Link
                    href={`/indicadores/${indicator.slug}`}
                    className="py-4 flex items-center justify-between gap-4 group"
                  >
                    <span className="min-w-0 text-base font-medium group-hover:underline underline-offset-2">
                      {indicator.name}
                    </span>
                    <span className="flex items-center gap-4 shrink-0">
                      {indicator.last_value !== null ? (
                        <span className="stat-figure text-lg font-semibold">
                          {formatNumber(indicator.last_value, indicator.unit)}
                        </span>
                      ) : (
                        <span className="text-sm text-gray-500">Sem dados</span>
                      )}
                      <ClassificationBadge classification={indicator.classification} />
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </section>
      ))}
    </>
  );
}
