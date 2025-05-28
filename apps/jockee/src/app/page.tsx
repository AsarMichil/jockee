'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authApi } from '../lib/api/auth';
import Image from "next/image";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    const checkAuth = async () => {
      const status = await authApi.getStatus();
      if (status.authenticated) {
      router.push('/dashboard');
      } else {
        router.push('/login');
      }
    };
    checkAuth();
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  );
}
