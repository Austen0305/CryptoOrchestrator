import { createFileRoute } from '@tanstack/react-router'
import { Link } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  component: Index,
})

function Index() {
  return (
    <div className="h-screen w-screen bg-background flex items-center justify-center relative overflow-hidden">
      {/* Background Gradients */}
      <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-background via-background/90 to-background/80 -z-10" />
      <div className="absolute -top-1/2 left-1/2 w-[1000px] h-[1000px] bg-primary/10 rounded-full blur-[100px] -translate-x-1/2 -z-20 animate-pulse" />
      
      <div className="flex flex-col gap-6 p-12 bg-card/10 backdrop-blur-md rounded-2xl border border-border shadow-2xl max-w-md w-full relative z-10">
        <div className="w-16 h-16 bg-accent rounded-full flex items-center justify-center text-3xl mx-auto shadow-lg shadow-accent/20">
          ⚡
        </div>
        
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold text-foreground tracking-tight">
            CryptoOrchestrator
            <span className="text-primary ml-1">.2026</span>
          </h1>
          
          <p className="text-lg text-muted-foreground leading-relaxed">
            Institutional-grade local trading engine.
            <br />
            Powered by <b className="text-foreground">Rust</b> & <b className="text-foreground">Polars</b>.
          </p>
        </div>
        
        <div className="h-4" />
        
        <Link 
          to="/login"
          className="bg-primary text-primary-foreground px-8 py-4 rounded-lg font-bold text-lg cursor-pointer transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-primary/20 hover:bg-primary/90 text-center block w-full"
        >
          Launch Terminal
        </Link>
        
        <div className="mt-8 flex justify-center gap-4 text-sm text-muted-foreground">
          <span>SLSA Level 3</span>
          <span>•</span>
          <span>MiCA Compliant</span>
          <span>•</span>
          <span>End-to-End Encrypted</span>
        </div>
      </div>
    </div>
  )
}
