import { ImageResponse } from "next/og";
import { getIndicatorDetail } from "@/lib/api";
import { formatDate, formatNumber } from "@/lib/format";
import { BrandOgImage, IndicatorOgImage, OG_CONTENT_TYPE, OG_SIZE } from "@/lib/og";

export const alt = "Indicador — Instituto Fiscaliza Brasil";
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;

type Params = { slug: string };

export default async function Image({ params }: { params: Promise<Params> }) {
  const { slug } = await params;
  const { detail } = await getIndicatorDetail(slug);
  const summary = detail?.summary ?? null;

  if (!detail || summary === null || summary.last_value === null) {
    return new ImageResponse(<BrandOgImage />, size);
  }

  return new ImageResponse(
    (
      <IndicatorOgImage
        name={detail.name}
        valueLabel={formatNumber(summary.last_value, detail.unit)}
        classification={summary.classification}
        dateLabel={summary.last_date ? formatDate(summary.last_date) : null}
        sourceName={detail.source_name}
      />
    ),
    size
  );
}
