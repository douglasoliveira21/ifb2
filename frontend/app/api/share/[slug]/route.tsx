import { ImageResponse } from "next/og";
import { NextRequest } from "next/server";
import { getIndicatorDetail } from "@/lib/api";
import { formatDate, formatNumber } from "@/lib/format";
import { Classification } from "@/lib/types";

const CLASSIFICATION_CONFIG: Record<Classification, { label: string; color: string }> = {
  MELHOROU: { label: "MELHOROU", color: "#1f7a3d" },
  PIOROU: { label: "PIOROU", color: "#b3261e" },
  ESTAVEL: { label: "ESTÁVEL", color: "#656565" },
  INCONCLUSIVO: { label: "INCONCLUSIVO", color: "#656565" },
  SEM_DADOS: { label: "SEM DADOS ATUALIZADOS", color: "#656565" },
};

type Params = { slug: string };

export async function GET(_req: NextRequest, { params }: { params: Promise<Params> }) {
  const { slug } = await params;
  const { detail } = await getIndicatorDetail(slug);

  const summary = detail?.summary ?? null;
  if (!detail || summary === null || summary.last_value === null) {
    return new Response("Indicador não encontrado ou sem dado disponível", { status: 404 });
  }
  const lastValue = summary.last_value;

  const classification = CLASSIFICATION_CONFIG[summary.classification];

  return new ImageResponse(
    (
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

        <div style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ fontSize: 28, color: "#656565", display: "flex" }}>{detail.name}</div>
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
            {formatNumber(lastValue, detail.unit)}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 16 }}>
            <div style={{ fontSize: 22, fontWeight: 700, color: classification.color, display: "flex" }}>
              {classification.label}
            </div>
            {summary.last_date && (
              <div style={{ fontSize: 20, color: "#656565", display: "flex" }}>
                {formatDate(summary.last_date)}
              </div>
            )}
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
          <div style={{ display: "flex" }}>Fonte: {detail.source_name}</div>
          <div style={{ display: "flex" }}>institutofiscalizabrasil.org</div>
        </div>
      </div>
    ),
    {
      width: 1200,
      height: 630,
      headers: {
        "Content-Disposition": `attachment; filename="ifb-${slug}.png"`,
      },
    }
  );
}
