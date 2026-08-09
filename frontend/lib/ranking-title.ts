import { Polarity } from "./types";

export function rankingTitle(indicatorName: string, polarity: Polarity): string {
  if (polarity === "lower_is_better") return `Estados onde ${indicatorName} mais caiu`;
  if (polarity === "higher_is_better") return `Estados onde ${indicatorName} mais subiu`;
  return `Estados por variação de ${indicatorName}`;
}
