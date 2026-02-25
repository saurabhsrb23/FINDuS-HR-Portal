"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { getToken } from "@/lib/auth";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    // If a token exists in sessionStorage, go to dashboard; otherwise login
    if (getToken()) {
      router.replace("/dashboard/jobs");
    } else {
      router.replace("/login");
    }
  }, [router]);

  // Brief blank screen while redirecting
  return null;
}
