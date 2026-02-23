import { Button } from '@/shared/ui/button'

export default function Home() {
  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col items-center justify-center gap-4">
      <h1 className="text-3xl font-bold text-blue-500">OptSolver Agent</h1>
      <p className="text-muted-foreground">Paper review and analysis tool.</p>
      <div className="flex gap-2">
        <Button>Get Started</Button>
        <Button variant="outline">Learn More</Button>
        <Button variant="secondary">Settings</Button>
      </div>
    </div>
  )
}
