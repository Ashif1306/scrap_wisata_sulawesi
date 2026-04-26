import './globals.css'

export const metadata = {
  title: 'Sulawesi Tourism Intelligence',
  description: 'Premium Explorer Dashboard for K-Nearest Neighbors Analysis.',
  icons: {
    icon: '/favicon.svg',
    shortcut: '/icon/favicon.png', // Fallback jika browser kurang support SVG
    apple: '/icon/favicon.png'
  }
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
