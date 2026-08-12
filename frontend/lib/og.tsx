import { Classification } from "@/lib/types";

export const OG_SIZE = { width: 1200, height: 630 };
export const OG_CONTENT_TYPE = "image/png";

const CLASSIFICATION_CONFIG: Record<Classification, { label: string; color: string }> = {
  MELHOROU: { label: "MELHOROU", color: "#1f7a3d" },
  PIOROU: { label: "PIOROU", color: "#b3261e" },
  ESTAVEL: { label: "ESTÁVEL", color: "#656565" },
  INCONCLUSIVO: { label: "INCONCLUSIVO", color: "#656565" },
  SEM_DADOS: { label: "SEM DADOS ATUALIZADOS", color: "#656565" },
};

function Wordmark() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          width: 44,
          height: 44,
          backgroundColor: "#111111",
          color: "#f5c400",
          fontWeight: 700,
          fontSize: 18,
        }}
      >
        IFB
      </div>
      <div style={{ fontSize: 16, fontWeight: 600, letterSpacing: 1, color: "#111111" }}>
        INSTITUTO FISCALIZA BRASIL
      </div>
    </div>
  );
}

export function BrandOgImage() {
  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        backgroundColor: "#ffffff",
        padding: "64px 72px",
        fontFamily: "sans-serif",
      }}
    >
      <Wordmark />
      <div style={{ display: "flex", flexDirection: "column" }}>
        <div
          style={{
            fontSize: 72,
            fontWeight: 800,
            color: "#111111",
            letterSpacing: "-0.02em",
            display: "flex",
            maxWidth: 900,
          }}
        >
          O Brasil pelos números.
        </div>
        <div style={{ fontSize: 26, color: "#656565", display: "flex", marginTop: 16 }}>
          Fiscalizamos resultados, não discursos.
        </div>
      </div>
      <div style={{ display: "flex", fontSize: 18, color: "#656565" }}>institutofiscalizabrasil.org</div>
    </div>
  );
}

export function IndicatorOgImage({
  name,
  locationLabel,
  valueLabel,
  classification,
  dateLabel,
  sourceName,
}: {
  name: string;
  locationLabel?: string;
  valueLabel: string;
  classification: Classification | null;
  dateLabel: string | null;
  sourceName: string;
}) {
  const config = classification ? CLASSIFICATION_CONFIG[classification] : null;

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        backgroundColor: "#ffffff",
        padding: "64px 72px",
        fontFamily: "sans-serif",
      }}
    >
      <Wordmark />

      <div style={{ display: "flex", flexDirection: "column" }}>
        <div style={{ fontSize: 28, color: "#656565", display: "flex" }}>
          {name}
          {locationLabel ? ` — ${locationLabel}` : ""}
        </div>
        <div
          style={{
            fontSize: 116,
            fontWeight: 800,
            color: "#111111",
            letterSpacing: "-0.02em",
            display: "flex",
            marginTop: 8,
          }}
        >
          {valueLabel}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 16 }}>
          {config && (
            <div style={{ fontSize: 22, fontWeight: 700, color: config.color, display: "flex" }}>
              {config.label}
            </div>
          )}
          {dateLabel && <div style={{ fontSize: 20, color: "#656565", display: "flex" }}>{dateLabel}</div>}
        </div>
      </div>

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          borderTop: "2px solid #111111",
          paddingTop: 16,
          fontSize: 18,
          color: "#656565",
        }}
      >
        <div style={{ display: "flex" }}>Fonte: {sourceName}</div>
        <div style={{ display: "flex" }}>institutofiscalizabrasil.org</div>
      </div>
    </div>
  );
}
