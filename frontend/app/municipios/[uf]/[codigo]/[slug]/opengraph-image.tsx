import { ImageResponse } from "next/og";
import { getIndicatorDetail, getMunicipioDetail } from "@/lib/api";
import { formatDate, formatNumber } from "@/lib/format";
import { BrandOgImage, IndicatorOgImage, OG_CONTENT_TYPE, OG_SIZE } from "@/lib/og";

export const alt = "Indicador por município — Instituto Fiscaliza Brasil";
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;

type Params = { uf: string; codigo: string; slug: string };

export default async function Image({ params }: { params: Promise<Params> }) {
  const { uf, codigo, slug } = await params;
  const [{ detail }, municipio] = await Promise.all([
    getIndicatorDetail(slug, codigo),
    getMunicipioDetail(uf, codigo),
  ]);
  const summary = detail?.summary ?? null;

  if (!detail || !municipio || summary === null || summary.last_value === null) {
    return new ImageResponse(<BrandOgImage />, size);
  }

  return new ImageResponse(
    (
      <IndicatorOgImage
        name={detail.name}
        locationLabel={`${municipio.name} (${municipio.uf})`}
        valueLabel={formatNumber(summary.last_value, detail.unit)}
        classification={summary.classification}
        dateLabel={summary.last_date ? formatDate(summary.last_date) : null}
        sourceName={detail.source_name}
      />
    ),
    size
  );
}
