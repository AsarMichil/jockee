import { analysisApi } from "@/lib/api/analysis";
import { useParams } from "react-router-dom";
import { Suspense } from "react";
import Player from "../components/player/Player";

export default function MixPage() {
  const { jobId } = useParams<{ jobId: string }>();

  if (!jobId) {
    return <div>Job ID not found</div>;
  }

  const data = analysisApi.getJobResults(jobId);
  console.log("data", data);

  return (
    <div>
      <Suspense
        fallback={
          <div className="min-h-screen flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        }
      >
        <Player data={data} />
      </Suspense>
    </div>
  );
}
