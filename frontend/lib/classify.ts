import { Classification, Polarity } from "./types";

export function classify(polarity: Polarity, first: number, last: number): Classification {
  if (last === first) return "ESTAVEL";
  if (polarity === "neutral") return "INCONCLUSIVO";
  const improved = polarity === "higher_is_better" ? last > first : last < first;
  return improved ? "MELHOROU" : "PIOROU";
}
