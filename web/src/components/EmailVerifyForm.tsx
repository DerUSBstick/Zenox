import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

interface Props {
  onSubmit: (result: { code: string }) => void
  submitting: boolean
}

export function EmailVerifyForm({ onSubmit, submitting }: Props) {
  const [code, setCode] = useState('')

  return (
    <form
      className="space-y-4 mt-4"
      onSubmit={(e) => {
        e.preventDefault()
        if (code.length >= 4) onSubmit({ code })
      }}
    >
      <p className="text-sm text-muted-foreground">
        HoYoLAB sent a verification code to your registered email address.
        Enter it below:
      </p>
      <Input
        type="text"
        inputMode="numeric"
        placeholder="123456"
        maxLength={8}
        value={code}
        onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
        className="text-center text-lg tracking-widest font-mono"
        autoFocus
      />
      <Button
        type="submit"
        className="w-full"
        disabled={submitting || code.length < 4}
      >
        {submitting ? 'Verifying…' : 'Submit Code'}
      </Button>
    </form>
  )
}
