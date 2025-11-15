import { useState, useEffect } from 'react'
import axios from 'axios'
import { LogIn, UserPlus, ShieldCheck } from 'lucide-react'
import './AuthSection.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function AuthSection({ onAuthChange }) {
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const token = localStorage.getItem('lexivion_token')
    const userEmail = localStorage.getItem('lexivion_user_email')
    if (token && userEmail) {
      onAuthChange({ token, email: userEmail })
    }
  }, [onAuthChange])

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const path = mode === 'login' ? '/api/auth/login' : '/api/auth/signup'
      const res = await axios.post(`${API_URL}${path}`, { email, password }, { headers: { 'Content-Type': 'application/json' } })
      const { token, user } = res.data
      localStorage.setItem('lexivion_token', token)
      localStorage.setItem('lexivion_user_email', user.email)
      onAuthChange({ token, email: user.email })
      setEmail('')
      setPassword('')
    } catch (err) {
      setError(err.response?.data?.error || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  const signOut = () => {
    localStorage.removeItem('lexivion_token')
    localStorage.removeItem('lexivion_user_email')
    onAuthChange(null)
  }

  const token = localStorage.getItem('lexivion_token')
  const userEmail = localStorage.getItem('lexivion_user_email')
  const isAuthed = Boolean(token && userEmail)

  return (
    <div className="auth-section">
      <div className="section-header">
        <ShieldCheck size={24} />
        <h2>User Access</h2>
      </div>
      {isAuthed ? (
        <div className="auth-status">
          <div className="user-chip">
            <span>{userEmail}</span>
          </div>
          <button className="signout-btn" onClick={signOut}>Sign Out</button>
        </div>
      ) : (
        <form onSubmit={submit} className="auth-form">
          <div className="auth-toggle">
            <button type="button" className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>
              <LogIn size={18} />
              <span>Sign In</span>
            </button>
            <button type="button" className={mode === 'signup' ? 'active' : ''} onClick={() => setMode('signup')}>
              <UserPlus size={18} />
              <span>Sign Up</span>
            </button>
          </div>
          <div className="auth-fields">
            <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required disabled={loading} />
            <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required disabled={loading} />
          </div>
          {error && <div className="auth-error">{error}</div>}
          <button type="submit" className="auth-submit" disabled={loading}>
            {loading ? 'Processing…' : mode === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>
      )}
    </div>
  )
}

export default AuthSection