import { useCallback, useEffect, useRef, useState } from 'react'
import type { GeetestV4Result } from '@/lib/types'
import { Button } from '@/components/ui/button'

interface Props {
  captchaId: string
  challenge?: string
  riskType?: string
  apiServer?: string
  onSuccess: (result: GeetestV4Result) => void
}

interface V4CaptchaObject {
  appendTo?: (element: Element | string) => void
  onSuccess: (callback: () => void) => void
  onReady?: (callback: () => void) => void
  showCaptcha?: () => void
  showBox?: () => void
  verify?: () => void
  getValidate: () => Omit<GeetestV4Result, 'captcha_id'>
}

interface InitGeetest4Config {
  captchaId: string
  product: string
  language: string
  apiServer: string
  challenge?: string
  riskType?: string
}

declare global {
  interface Window {
    initGeetest4?: (
      config: InitGeetest4Config,
      callback: (captcha: V4CaptchaObject) => void,
    ) => void
  }
}

export function GeetestV4({ captchaId, riskType, apiServer, onSuccess }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const captchaRef = useRef<V4CaptchaObject | null>(null)
  const startedRef = useRef(false)
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading')
  const [errorMessage, setErrorMessage] = useState('')

  const openCaptcha = useCallback(() => {
    const cap = captchaRef.current
    if (!cap) return
    // SDK variants expose different open methods.
    cap.showCaptcha?.()
    cap.showBox?.()
    cap.verify?.()
  }, [])

  useEffect(() => {
    let cancelled = false

    if (startedRef.current) {
      return () => {
        cancelled = true
      }
    }
    startedRef.current = true

    if (!captchaId) {
      setStatus('error')
      setErrorMessage(
        'Missing captcha_id/gt in challenge payload. Check bot logs for x-rpc-aigis parsing.',
      )
      return
    }

    const script = document.createElement('script')
    script.src = 'https://static.geetest.com/v4/gt4.js'
    script.onerror = () => {
      if (cancelled) return
      setStatus('error')
      setErrorMessage(
        'Failed to load Geetest script from static.geetest.com. Disable blockers/firewall rules and refresh.',
      )
    }
    script.onload = () => {
      if (cancelled) return
      if (!containerRef.current || !window.initGeetest4) {
        setStatus('error')
        setErrorMessage('Geetest v4 initializer did not load correctly.')
        return
      }
      // Use the api_server from HoYo's AIGIS challenge data if provided;
      // otherwise fall back to the standard Geetest v4 server.
      const resolvedApiServer = apiServer || 'gcaptcha4.geetest.com'
      const initConfig: Parameters<NonNullable<typeof window.initGeetest4>>[0] = {
        captchaId,
        // Bind mode renders inline and avoids popup blockers in development.
        product: 'bind',
        language: 'eng',
        apiServer: resolvedApiServer,
      }
      // Only include riskType when non-empty – passing empty strings can
      // confuse the Geetest SDK. 'challenge' is intentionally NOT forwarded:
      // genshin.py's MMTv4 model excludes it so the SDK generates its own
      // Geetest challenge, which is what HoYo validates against.
      if (riskType) initConfig.riskType = riskType
      window.initGeetest4(
        initConfig,
        (captcha) => {
          if (cancelled) return
          captchaRef.current = captcha

          if (captcha.appendTo && containerRef.current) {
            captcha.appendTo(containerRef.current)
          }

          setStatus('ready')

          if (captcha.onReady) {
            captcha.onReady(() => {
              if (cancelled) return
              openCaptcha()
            })
          }

          captcha.onSuccess(() => {
            const v = captcha.getValidate()
            onSuccess({ captcha_id: captchaId, ...v })
          })
        },
      )
    }
    document.head.appendChild(script)

    return () => {
      cancelled = true
      if (document.head.contains(script)) document.head.removeChild(script)
      captchaRef.current = null
      startedRef.current = false
    }
  }, [captchaId, riskType, apiServer, onSuccess, openCaptcha])

  return (
    <div className="mt-2 space-y-3">
      {status === 'loading' && (
        <p className="text-sm text-muted-foreground text-center">
          Loading Geetest challenge...
        </p>
      )}
      {status === 'ready' && (
        <div className="flex flex-col items-center gap-2">
          <Button
            type="button"
            onClick={openCaptcha}
          >
            Start Verification
          </Button>
          <p className="text-xs text-muted-foreground text-center">
            If the inline widget did not activate automatically, click the button above.
          </p>
        </div>
      )}
      {status === 'error' && (
        <div className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
          <p className="font-medium">Could not render captcha</p>
          <p className="mt-1">{errorMessage}</p>
          <p className="mt-2 text-xs">Challenge captchaId: {captchaId || 'n/a'}</p>
          <p className="text-xs">riskType: {riskType || 'n/a'}</p>
        </div>
      )}
      <div ref={containerRef} className="flex justify-center min-h-12" />
    </div>
  )
}
