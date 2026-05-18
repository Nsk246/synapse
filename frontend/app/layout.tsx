import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Synapse — Semantic Observability',
  description: 'Real-time semantic drift detection for multi-agent LLM pipelines',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0a0a0f] text-[#e2e2f0] antialiased">
        {children}
      </body>
    </html>
  )
}
