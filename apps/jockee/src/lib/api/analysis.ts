import { apiClient } from "./client";
import { AnalysisJob, MixInstructions } from "../types";

export const analysisApi = {
  // Get job status
  getJobStatus: async (jobId: string): Promise<AnalysisJob> => {
    return await apiClient.get<AnalysisJob>(`/api/v1/jobs/${jobId}/status`);
  },

  // Get complete job results with tracks and mix instructions
  getJobResults: async (jobId: string): Promise<AnalysisJob> => {
    return await apiClient.get<AnalysisJob>(`/api/v1/jobs/${jobId}/results`);
  },

  // Get mix instructions
  getMixInstructions: async (jobId: string): Promise<MixInstructions> => {
    return await apiClient.get<MixInstructions>(`/api/v1/jobs/${jobId}/mix`);
  },

  // Get all user jobs
  getUserJobs: async (): Promise<AnalysisJob[]> => {
    return await apiClient.get<AnalysisJob[]>("/api/v1/jobs");
  },

  // Cancel job
  cancelJob: async (jobId: string): Promise<void> => {
    await apiClient.delete<void>(`/api/v1/jobs/${jobId}`);
  },

  // Get audio file URL for a track
  getTrackAudioUrl: async (trackId: string): Promise<{ url: string }> => {
    return await apiClient.get<{ url: string }>(
      `/api/v1/tracks/${trackId}/audio/url`
    );
  },

  // Download mix as file
  downloadMix: async (jobId: string): Promise<Blob> => {
    return await apiClient.get<Blob>(`/api/v1/jobs/${jobId}/download`);
  }
};
