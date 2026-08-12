import './globals.css'
import { Toaster } from '@/components/ui/sonner'

export const metadata = {
  title: 'YükTakip - Lojistik Operasyon Paneli',
  description: 'Yük toplama, planlama ve iç nakliye takip sistemi',
}

export default function RootLayout({ children }) {
  return (
    <html lang="tr">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        {children}
        <Toaster position="top-right" richColors />
      </body>
    </html>
  )
}
