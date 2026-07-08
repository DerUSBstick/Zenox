import { CheckCircle2, Radio } from 'lucide-react'
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface Props {
  success?: boolean
}

export function StatusView({ success = false }: Props) {
  return (
    <Card className="w-full max-w-lg">
      <CardHeader className="text-center">
        <div className="flex justify-center mb-3">
          {success ? (
            <CheckCircle2 className="h-12 w-12 text-green-500" />
          ) : (
            <Radio className="h-12 w-12 text-blue-400 animate-pulse" />
          )}
        </div>
        <CardTitle>
          {success ? 'Challenge Solved!' : 'Waiting for Challenge'}
        </CardTitle>
        <CardDescription className="mt-2">
          {success
            ? 'The bot is completing the HoYoLAB login. You can close this window.'
            : 'No pending challenges. This page updates automatically when the bot needs help.'}
        </CardDescription>
        <div className="flex justify-center mt-4">
          <Badge
            variant={success ? 'default' : 'secondary'}
            className="gap-1.5"
          >
            <span
              className={`inline-block h-2 w-2 rounded-full ${
                success ? 'bg-green-400' : 'bg-blue-400 animate-pulse'
              }`}
            />
            {success ? 'Login in progress' : 'Listening'}
          </Badge>
        </div>
      </CardHeader>
    </Card>
  )
}
