import { analysisApi } from "@/lib/api/analysis";
import { useParams, useNavigate } from "react-router-dom";
import { Suspense } from "react";
import Player from "../components/player/Player";

export default function MixPage() {
  const navigate = useNavigate();
  const { jobId } = useParams<{ jobId: string }>();
  
  if (!jobId) {
    return <div>Job ID not found</div>;
  }
  
  const data = analysisApi.getJobResults(jobId);
  console.log("data", data);
  
  return (
    <div>
      <div onClick={() => navigate(`/mix/${jobId}`)}>MixPage</div>
      <div onClick={() => navigate(`/dashboard`)}>Dashboard</div>
      <Suspense fallback={<div>Loading...</div>}>
        <Player data={data} />
      </Suspense>
    </div>
  );
} 