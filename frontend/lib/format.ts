export function formatNumber(value: number, unit: string): string {
  const decimals = unit === "R$" || Math.abs(value) >= 1000 ? 0 : 1;
  const formatted = new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
  if (unit === "%") return `${formatted}%`;
  if (unit === "R$") return `R$ ${formatted}`;
  return `${formatted} ${unit}`;
}

export function formatDate(isoDate: string): string {
  const [year, month] = isoDate.split("-");
  const months = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
  ];
  return `${months[Number(month) - 1]}/${year}`;
}
