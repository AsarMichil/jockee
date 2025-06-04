import { Routes, Route, Navigate } from 'react-router-dom'
import { AudioStoreProvider } from '@/lib/audio/AudioStoreProvider'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import CallbackPage from './pages/CallbackPage'
import DashboardPage from './pages/DashboardPage'
import AnalysisPage from './pages/AnalysisPage'
import MixPage from './pages/MixPage'

function App() {
  return (
    <div className="font-geist-sans antialiased">
      <AudioStoreProvider>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/callback" element={<CallbackPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/analysis/:jobId" element={<AnalysisPage />} />
          <Route path="/mix/:jobId" element={<MixPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AudioStoreProvider>
    </div>
  )
}

export default App 