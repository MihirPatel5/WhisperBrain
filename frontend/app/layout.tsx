import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'WhisperBrain',
  description: 'Real-time voice conversation with LLM',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

