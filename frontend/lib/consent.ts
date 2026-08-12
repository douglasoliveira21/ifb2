import { useSyncExternalStore } from "react";

export const CONSENT_STORAGE_KEY = "ifb-cookie-consent";
export const CONSENT_CHANGE_EVENT = "ifb-consent-change";

export type ConsentValue = "accepted" | "rejected";

export function getStoredConsent(): ConsentValue | null {
  if (typeof window === "undefined") return null;
  const value = window.localStorage.getItem(CONSENT_STORAGE_KEY);
  return value === "accepted" || value === "rejected" ? value : null;
}

export function setStoredConsent(value: ConsentValue) {
  window.localStorage.setItem(CONSENT_STORAGE_KEY, value);
  window.dispatchEvent(new CustomEvent<ConsentValue>(CONSENT_CHANGE_EVENT, { detail: value }));
}

function subscribeToConsentChanges(callback: () => void) {
  window.addEventListener(CONSENT_CHANGE_EVENT, callback);
  window.addEventListener("storage", callback);
  return () => {
    window.removeEventListener(CONSENT_CHANGE_EVENT, callback);
    window.removeEventListener("storage", callback);
  };
}

function getServerConsentSnapshot(): ConsentValue | null {
  return null;
}

export function useConsent(): ConsentValue | null {
  return useSyncExternalStore(subscribeToConsentChanges, getStoredConsent, getServerConsentSnapshot);
}
