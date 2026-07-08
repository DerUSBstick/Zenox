import { useEffect, useRef, useState } from 'react'
import type { GeetestV3Result } from '@/lib/types'

interface Props {
  gt: string
  challenge: string
  newCaptcha: number
  onSuccess: (result: GeetestV3Result) => void
}

interface V3CaptchaObject {
  appendTo: (element: Element) => void
  onSuccess: (callback: () => void) => void
  getValidate: () => GeetestV3Result
}

declare global {
  interface Window {
    initGeetest?: (
      config: {
        gt: string
        challenge: string
        new_captcha: number
        product: string
        lang: string
      },
      callback: (captchaObj: V3CaptchaObject) => void,
    ) => void
  }
}

export function GeetestV3({ gt, challenge, newCaptcha, onSuccess }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const startedRef = useRef(false)
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading')
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    let cancelled = false

    if (startedRef.current) {
      return () => {
        cancelled = true
      }
    }
    startedRef.current = true

    if (!gt || !challenge) {
      setStatus('error')
      setErrorMessage(
        'Missing gt/challenge in challenge payload. Check bot logs for x-rpc-aigis parsing.',
      )
      return
    }

    const init = () => {
      if (cancelled) return
      if (!containerRef.current || !window.initGeetest) {
        setStatus('error')
        setErrorMessage('Geetest v3 initializer did not load correctly.')
        return
      }
      window.initGeetest(
        { gt, challenge, new_captcha: newCaptcha, product: 'bind', lang: 'en' },
        (captchaObj) => {
          if (cancelled) return
          captchaObj.appendTo(containerRef.current!)
          setStatus('ready')
          captchaObj.onSuccess(() => onSuccess(captchaObj.getValidate()))
        },
      )
    }

    if (window.initGeetest) {
      init()
      return
    }

    const script = document.createElement('script')
    script.src = 'https://static.geetest.com/static/js/gt.min.js'
    script.onerror = () => {
      if (cancelled) return
      setStatus('error')
      setErrorMessage(
        'Failed to load Geetest script from static.geetest.com. Disable blockers/firewall rules and refresh.',
      )
    }
    script.onload = init
    document.head.appendChild(script)

    return () => {
      cancelled = true
      if (document.head.contains(script)) document.head.removeChild(script)
      startedRef.current = false
    }
  }, [gt, challenge, newCaptcha, onSuccess])

  return (
    <div className="mt-2 space-y-3">
      {status === 'loading' && (
        <p className="text-sm text-muted-foreground text-center">
          Loading Geetest challenge...
        </p>
      )}
      {status === 'error' && (
        <div className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
          <p className="font-medium">Could not render captcha</p>
          <p className="mt-1">{errorMessage}</p>
          <p className="mt-2 text-xs">Challenge gt: {gt || 'n/a'}</p>
        </div>
      )}
      <div ref={containerRef} className="flex justify-center" />
    </div>
  )
}
