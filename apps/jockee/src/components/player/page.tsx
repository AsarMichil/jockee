"use client";

import { analysisApi } from "@/lib/api/analysis";
import { useParams, useRouter } from "next/navigation";
import { Suspense } from "react";
import Player from "./Player";

export default function MixPage() {
  const router = useRouter();
  const params = useParams();
  const jobId = params.jobId as string;
  const data = analysisApi.getJobResults(jobId);
  console.log("data", data);
  return (
    <div>
      <div onClick={() => router.push(`/mix/${jobId}`)}>MixPage</div>
      <div onClick={() => router.push(`/dashboard`)}>Dashboard</div>
      <Suspense fallback={<div>Loading...</div>}>
        <Player data={data} />
      </Suspense>
    </div>
  );
}
