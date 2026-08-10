import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getCompareIndicators, getGovernmentPeriods, getStates } from "@/lib/api";
import { formatDate } from "@/lib/format";
import GovernmentPeriodTable from "@/components/GovernmentPeriodTable";

type Params = { locationCode: string; periodId: string };

async function loadPeriod(locationCode: string, periodId: string) {
  const periods = await getGovernmentPeriods(locationCode);
  return periods.find((p) => p.id === periodId) ?? null;
}

async function locationName(locationCode: string): Promise<string> {
  if (locationCode.toUpperCase() === "BR") return "Brasil";
  const { states } = await getStates();
  return states.find((s) => s.code === locationCode.toUpperCase())?.name ?? locationCode.toUpperCase();
}

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { locationCode, periodId } = await params;
  const period = await loadPeriod(locationCode, periodId);
  if (!period) return { title: "Mandato não encontrado — Instituto Fiscaliza Brasil" };
  return {
    title: `${period.holder_name} — Instituto Fiscaliza Brasil`,
    description: `Indicadores no início e no fim do mandato de ${period.holder_name}.`,
  };
}

export default async function GovernmentPeriodPage({ params }: { params: Promise<Params> }) {
  const { locationCode, periodId } = await params;
  const period = await loadPeriod(locationCode, periodId);

  if (!period) notFound();

  const [{ indicators }, locName] = await Promise.all([
    getCompareIndicators(locationCode),
    locationName(locationCode),
  ]);

  return (
    <>
      <section className="mx-auto max-w-3xl px-4 sm:px-6 pt-10 sm:pt-16 pb-6">
        <Link href="/governo" className="text-sm text-gray-500 hover:text-ink underline underline-offset-2">
          ← Ficha por Governante
        </Link>
        <h1 className="mt-4 text-3xl sm:text-5xl font-extrabold tracking-tight">{period.holder_name}</h1>
        <p className="mt-3 text-lg text-gray-500">
          {locName} — {formatDate(period.start_date)} a{" "}
          {period.end_date ? formatDate(period.end_date) : "atual"}
        </p>
      </section>

      <section className="border-t border-ink">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 py-8">
          <GovernmentPeriodTable indicators={indicators} period={period} />
        </div>
      </section>
    </>
  );
}
