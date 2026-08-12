"use client";

import { useEffect, useState } from "react";

export default function ScrollCue() {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    function handleScroll() {
      const scrolledPast = window.scrollY > 80;
      const nearBottom = window.innerHeight + window.scrollY >= document.body.scrollHeight - 80;
      setVisible(!scrolledPast && !nearBottom);
    }
    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });
    window.addEventListener("resize", handleScroll);
    return () => {
      window.removeEventListener("scroll", handleScroll);
      window.removeEventListener("resize", handleScroll);
    };
  }, []);

  if (!visible) return null;

  return (
    <div aria-hidden className="pointer-events-none fixed inset-x-0 bottom-0 z-30 h-16">
      <div className="absolute inset-0 bg-gradient-to-t from-paper to-transparent" />
      <svg
        className="absolute inset-x-0 bottom-2 mx-auto animate-bounce"
        width="20"
        height="20"
        viewBox="0 0 20 20"
        fill="none"
      >
        <path
          d="M4 8l6 6 6-6"
          stroke="var(--color-gray-500)"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}
