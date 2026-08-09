import { IndicatorValuePoint } from "./types";

export interface PeriodValues {
  startValue: number | null;
  startDate: string | null;
  endValue: number | null;
  endDate: string | null;
}

/**
 * Valor mais próximo do início do período (primeiro ponto >= start) e do
 * fim do período (último ponto <= end; se o período ainda está em curso —
 * end null — usa o ponto mais recente disponível). Histórico já vem
 * ordenado por data (garantido pela API).
 */
export function valuesForPeriod(
  history: IndicatorValuePoint[],
  start: string,
  end: string | null
): PeriodValues {
  const startPoint = history.find((p) => p.reference_date >= start);
  const endPoint = end
    ? [...history].reverse().find((p) => p.reference_date <= end)
    : history[history.length - 1];

  return {
    startValue: startPoint?.value ?? null,
    startDate: startPoint?.reference_date ?? null,
    endValue: endPoint?.value ?? null,
    endDate: endPoint?.reference_date ?? null,
  };
}
