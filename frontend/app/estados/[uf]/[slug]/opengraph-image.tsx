import { ImageResponse } from "next/og";
import { getIndicatorDetail, getStateDetail } from "@/lib/api";
import { formatDate, formatNumber } from "@/lib/format";
import { BrandOgImage, IndicatorOgImage, OG_CONTENT_TYPE, OG_SIZE } from "@/lib/og";

export const alt = "Indicador por estado — Instituto Fiscaliza Brasil";
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;

type Params = { uf: string; slug: string };

export default async function Image({ params }: { params: Promise<Params> }) {
  const { uf, slug } = await params;
  const [{ detail }, { detail: state }] = await Promise.all([getIndicatorDetail(slug, uf), getStateDetail(uf)]);
  const summary = detail?.summary ?? null;

  if (!detail || !state || summary === null || summary.last_value === null) {
    return new ImageResponse(<BrandOgImage />, size);
  }

  return new ImageResponse(
    (
      <IndicatorOgImage
        name={detail.name}
        locationLabel={state.name}
        valueLabel={formatNumber(summary.last_value, detail.unit)}
        classification={summary.classification}
        dateLabel={summary.last_date ? formatDate(summary.last_date) : null}
        sourceName={detail.source_name}
      />
    ),
    size
  );
}
