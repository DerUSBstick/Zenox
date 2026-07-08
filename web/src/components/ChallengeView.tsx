import { ShieldAlert } from 'lucide-react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { Challenge } from '@/lib/types'
import { GeetestV3 } from './GeetestV3'
import { GeetestV4 } from './GeetestV4'
import { EmailVerifyForm } from './EmailVerifyForm'

const TYPE_LABELS: Record<string, string> = {
  geetest_v3: 'Geetest v3',
  geetest_v4: 'Geetest v4',
  email_verify: 'Email Verification',
}

interface Props {
  challenge: Challenge
  onSolve: (result: object) => void
  submitting: boolean
}

export function ChallengeView({ challenge, onSolve, submitting }: Props) {
  const d = challenge.data as Record<string, unknown>

  return (
    <Card className="w-full max-w-lg">
      <CardHeader>
        <div className="flex items-center gap-2">
          <ShieldAlert className="text-amber-500 h-5 w-5 flex-shrink-0" />w
          <CardTitle>HoYoLAB Authentication Required</CardTitle>
        </div>
        <CardDescription className="flex items-center flex-wrap gap-2 mt-1">
          The bot needs your help to complete the login.
          <Badge variant="outline">
            {TYPE_LABELS[challenge.type] ?? challenge.type}
          </Badge>
        </CardDescription>
      </CardHeader>
      <CardContent>
        {challenge.type === 'geetest_v3' && (
          <GeetestV3
            gt={String(d.gt ?? '')}
            challenge={String(d.challenge ?? '')}
            newCaptcha={Number(d.new_captcha ?? 1)}
            onSuccess={onSolve}
          />
        )}
        {challenge.type === 'geetest_v4' && (
          <GeetestV4
            captchaId={String(d.captcha_id ?? d.gt ?? '')}
            challenge={String(d.challenge ?? '')}
            riskType={String(d.risk_type ?? '')}
            apiServer={String(d.api_server ?? '')}
            onSuccess={onSolve}
          />
        )}
        {challenge.type === 'email_verify' && (
          <EmailVerifyForm onSubmit={onSolve} submitting={submitting} />
        )}
      </CardContent>
    </Card>
  )
}
