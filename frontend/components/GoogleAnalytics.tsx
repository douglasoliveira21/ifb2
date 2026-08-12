"use client";

import Script from "next/script";
import { useConsent } from "@/lib/consent";

const GA_ID = "G-8L1FRPH86R";

export default function GoogleAnalytics() {
  const consent = useConsent();

  if (consent !== "accepted") return null;

  return (
    <>
      <Script src={`https://www.googletagmanager.com/gtag/js?id=${GA_ID}`} strategy="afterInteractive" />
      <Script id="google-analytics" strategy="afterInteractive">
        {`window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', '${GA_ID}');`}
      </Script>
    </>
  );
}
