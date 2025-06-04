import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { authApi } from "../lib/api/auth";

export default function HomePage() {
  const navigate = useNavigate();

  useEffect(() => {
    const checkAuth = async () => {
      const status = await authApi.getStatus();
      if (status.authenticated) {
        navigate("/dashboard");
      } else {
        navigate("/login");
      }
    };
    checkAuth();
  }, [navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  );
} 