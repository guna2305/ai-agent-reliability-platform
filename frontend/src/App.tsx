import { Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { ProtectedRoute } from '@/components/layout/ProtectedRoute'
import { LoginPage } from '@/pages/Auth/LoginPage'
import { DashboardPage } from '@/pages/Dashboard/DashboardPage'
import { AgentsPage } from '@/pages/Agents/AgentsPage'
import { ExecutionsPage } from '@/pages/Executions/ExecutionsPage'
import { EvaluationsPage } from '@/pages/Evaluations/EvaluationsPage'
import { TracesPage } from '@/pages/Traces/TracesPage'
import { AnalyticsPage } from '@/pages/Analytics/AnalyticsPage'
import { FailuresPage } from '@/pages/Failures/FailuresPage'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="agents" element={<AgentsPage />} />
        <Route path="executions" element={<ExecutionsPage />} />
        <Route path="evaluations" element={<EvaluationsPage />} />
        <Route path="traces/:executionId" element={<TracesPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="failures" element={<FailuresPage />} />
      </Route>
    </Routes>
  )
}
