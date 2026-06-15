import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { GitBranch, Loader2 } from 'lucide-react'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/authStore'
import { useOrgStore } from '@/stores/orgStore'

export function LoginPage() {
  const navigate = useNavigate()
  const setSession = useAuthStore((s) => s.setSession)
  const setOrganizations = useOrgStore((s) => s.setOrganizations)

  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const tokens =
        mode === 'login'
          ? await authApi.login(email, password)
          : await authApi.register({ email, password, full_name: fullName })
      setSession(tokens)
      const orgs = await authApi.listOrganizations()
      setOrganizations(orgs)
      navigate('/dashboard')
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 px-4">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-3 mb-8 justify-center">
          <div className="w-10 h-10 bg-brand-600 rounded-lg flex items-center justify-center">
            <GitBranch className="w-5 h-5 text-white" />
          </div>
          <div>
            <p className="text-base font-semibold text-white leading-tight">Agent Platform</p>
            <p className="text-xs text-gray-400">Reliability Suite</p>
          </div>
        </div>

        <div className="card">
          <h1 className="text-lg font-semibold text-white mb-1">
            {mode === 'login' ? 'Sign in' : 'Create account'}
          </h1>
          <p className="text-sm text-gray-400 mb-6">
            {mode === 'login'
              ? 'Welcome back. Enter your credentials.'
              : 'Register — a personal organization is created for you.'}
          </p>

          <form onSubmit={submit} className="space-y-4">
            {mode === 'register' && (
              <Field label="Full name" value={fullName} onChange={setFullName} type="text" required />
            )}
            <Field label="Email" value={email} onChange={setEmail} type="email" required />
            <Field label="Password" value={password} onChange={setPassword} type="password" required />

            {error && (
              <p className="text-xs text-red-400 bg-red-900/20 border border-red-800 rounded-md px-3 py-2">
                {error}
              </p>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              {mode === 'login' ? 'Sign in' : 'Create account'}
            </button>
          </form>

          <button
            onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(null) }}
            className="mt-4 text-xs text-gray-400 hover:text-brand-400 w-full text-center"
          >
            {mode === 'login' ? "Don't have an account? Register" : 'Already have an account? Sign in'}
          </button>
        </div>
      </div>
    </div>
  )
}

function Field(props: {
  label: string
  value: string
  onChange: (v: string) => void
  type: string
  required?: boolean
}) {
  return (
    <label className="block">
      <span className="text-xs text-gray-400 font-medium">{props.label}</span>
      <input
        type={props.type}
        value={props.value}
        required={props.required}
        onChange={(e) => props.onChange(e.target.value)}
        className="mt-1 w-full bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500"
      />
    </label>
  )
}
