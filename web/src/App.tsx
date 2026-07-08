import { useState, useEffect, useCallback } from 'react'
import type { Challenge } from './lib/types'
import {
  fetchPendingChallenge,
  submitChallengeResult,
  connectToEvents,
} from './lib/api'
import { ChallengeView } from './components/ChallengeView'
import { StatusView } from './components/StatusView'

function InsecureContextBanner() {
  if (window.isSecureContext) return null
  return (
    <div className="w-full max-w-lg rounded-md border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-300 text-center">
      <p className="font-semibold">⚠ HTTPS required for captcha</p>
      <p className="mt-1 text-xs text-amber-400/80">
        Geetest needs a secure context to set its risk cookie. Start Chrome with:<br />
        <code className="font-mono text-xs break-all">
          chrome --unsafely-treat-insecure-origin-as-secure="{window.location.origin}"
          --user-data-dir="%TEMP%\chrome-secure"
        </code>
        <br />or use Firefox which allows Secure cookies on localhost.
        In production the HTTPS nginx proxy removes this issue.
      </p>
    </div>
  )
}

export default function App() {
  const [challenge, setChallenge] = useState<Challenge | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState(false)

  // Fetch current challenge state on mount
  useEffect(() => {
    fetchPendingChallenge().then(setChallenge).catch(console.error)
  }, [])

  // SSE: receive real-time challenge push/resolve events
  useEffect(() => {
    return connectToEvents((event) => {
      if (event.type === 'challenge_added') {
        setChallenge(event.challenge)
        setSuccess(false)
      } else if (event.type === 'challenge_resolved') {
        setChallenge((prev) => (prev?.id === event.id ? null : prev))
      }
    })
  }, [])

  const handleSolve = useCallback(
    async (result: object) => {
      if (!challenge) return
      setSubmitting(true)
      try {
        await submitChallengeResult(challenge.id, result)
        setSuccess(true)
        setChallenge(null)
      } catch (err) {
        console.error('Failed to submit result:', err)
        // Keep challenge visible so the user can retry
      } finally {
        setSubmitting(false)
      }
    },
    [challenge],
  )

  return (
    <main className="min-h-screen bg-background flex flex-col items-center justify-center p-4 gap-4">
      <InsecureContextBanner />
      <div className="text-center mb-2">
        <h1 className="text-2xl font-bold text-foreground tracking-tight">
          Zenox
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          HoYoLAB Authentication Dashboard
        </p>
      </div>

      {challenge ? (
        <ChallengeView
          challenge={challenge}
          onSolve={handleSolve}
          submitting={submitting}
        />
      ) : (
        <StatusView success={success} />
      )}
    </main>
  )
}
