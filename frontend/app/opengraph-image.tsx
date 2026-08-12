import { ImageResponse } from "next/og";
import { BrandOgImage, OG_CONTENT_TYPE, OG_SIZE } from "@/lib/og";

export const alt = "Instituto Fiscaliza Brasil — O Brasil pelos números";
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;

export default async function Image() {
  return new ImageResponse(<BrandOgImage />, size);
}
