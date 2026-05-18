'use client'
import dynamic from 'next/dynamic'
import AnatomyPanel    from '@/components/AnatomyPanel'
import DriftForensics  from '@/components/DriftForensics'

// Dynamically import canvas (React Flow requires browser APIs)
const SynapseCanvas = dynamic(() => import('@/components/SynapseCanvas'), { ssr: false })

export default function Home() {
  return (
    <main className="flex h-screen w-screen overflow-hidden bg-[#0a0a0f]">
      {/* Left — Anatomy Panel */}
      <aside className="w-72 flex-shrink-0 h-full">
        <AnatomyPanel />
      </aside>

      {/* Right — Flow Canvas */}
      <section className="flex-1 h-full relative">
        <SynapseCanvas />
      </section>

      {/* Overlay — Drift Forensics modal */}
      <DriftForensics />
    </main>
  )
}
