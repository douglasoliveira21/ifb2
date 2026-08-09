import { Classification } from "@/lib/types";

const CONFIG: Record<Classification, { label: string; icon: string; className: string }> = {
  MELHOROU: { label: "Melhorou", icon: "▲", className: "text-positive" },
  PIOROU: { label: "Piorou", icon: "▼", className: "text-negative" },
  ESTAVEL: { label: "Estável", icon: "■", className: "text-neutral" },
  INCONCLUSIVO: { label: "Inconclusivo", icon: "?", className: "text-neutral" },
  SEM_DADOS: { label: "Sem dados atualizados", icon: "…", className: "text-neutral" },
};

export default function ClassificationBadge({ classification }: { classification: Classification }) {
  const { label, icon, className } = CONFIG[classification];
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide ${className}`}>
      <span aria-hidden>{icon}</span>
      {label}
    </span>
  );
}
