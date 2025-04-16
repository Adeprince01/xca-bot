import { Inter } from 'next/font/google';
import '../styles/globals.css';
import { ThemeProvider } from './context/ThemeContext';
import ThemeToggle from './components/ThemeToggle';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'XCA Bot',
  description: 'Your AI assistant for XCA',
};

export default function RootLayout({ children }) {
  const pathname = typeof window !== 'undefined' ? window.location.pathname : '';

  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider>
          <div className="min-h-screen flex bg-gradient-to-b from-gray-50 via-white to-gray-100 dark:from-gray-900 dark:via-gray-950 dark:to-gray-900 text-gray-900 dark:text-white">
            {/* Sidebar Navigation */}
            <aside className="hidden md:flex flex-col w-20 bg-white/90 dark:bg-gray-900/90 border-r border-gray-200 dark:border-gray-800 shadow-sm py-6 items-center gap-8 sticky top-0 h-screen z-40">
              <div className="flex flex-col items-center gap-4 w-full">
                {/* Logo/Icon */}
                <div className="w-10 h-10 bg-blue-600 rounded-2xl flex items-center justify-center text-white font-extrabold text-2xl shadow-md mb-2">X</div>
                <nav className="flex flex-col gap-6 mt-8 w-full items-center">
                  <Link href="/" className={`w-12 h-12 flex items-center justify-center rounded-xl transition-colors ${pathname === '/' ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 shadow' : 'text-gray-400 dark:text-gray-500 hover:bg-blue-50 dark:hover:bg-gray-800 hover:text-blue-600 dark:hover:text-blue-300'}`}>🏠</Link>
                  <Link href="/matches" className={`w-12 h-12 flex items-center justify-center rounded-xl transition-colors ${pathname === '/matches' ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 shadow' : 'text-gray-400 dark:text-gray-500 hover:bg-blue-50 dark:hover:bg-gray-800 hover:text-blue-600 dark:hover:text-blue-300'}`}>📄</Link>
                  <Link href="/settings" className={`w-12 h-12 flex items-center justify-center rounded-xl transition-colors ${pathname === '/settings' ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 shadow' : 'text-gray-400 dark:text-gray-500 hover:bg-blue-50 dark:hover:bg-gray-800 hover:text-blue-600 dark:hover:text-blue-300'}`}>⚙️</Link>
                </nav>
                <div className="mt-auto mb-2"><ThemeToggle /></div>
              </div>
            </aside>
            {/* Main Content Area */}
            <div className="flex-1 flex flex-col min-h-screen">
              {/* Top Bar */}
              <header className="w-full flex items-center justify-between px-6 py-3 bg-white/80 dark:bg-gray-900/80 border-b border-gray-200 dark:border-gray-800 shadow-sm sticky top-0 z-30">
                <div className="flex items-center gap-3">
                  <span className="md:hidden w-10 h-10 bg-blue-600 rounded-2xl flex items-center justify-center text-white font-extrabold text-2xl shadow-md">X</span>
                  <h1 className="text-xl font-extrabold tracking-tight text-gray-900 dark:text-white">XCA-Bot Dashboard</h1>
                </div>
                <div className="flex items-center gap-4 md:hidden">
                  <Link href="/" className={`px-3 py-1 rounded-md font-medium transition-colors ${pathname === '/' ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 shadow' : 'text-gray-600 dark:text-gray-400 hover:bg-blue-50 dark:hover:bg-gray-800 hover:text-blue-600 dark:hover:text-blue-300'}`}>Dashboard</Link>
                  <Link href="/matches" className={`px-3 py-1 rounded-md font-medium transition-colors ${pathname === '/matches' ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 shadow' : 'text-gray-600 dark:text-gray-400 hover:bg-blue-50 dark:hover:bg-gray-800 hover:text-blue-600 dark:hover:text-blue-300'}`}>Matches</Link>
                  <Link href="/settings" className={`px-3 py-1 rounded-md font-medium transition-colors ${pathname === '/settings' ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 shadow' : 'text-gray-600 dark:text-gray-400 hover:bg-blue-50 dark:hover:bg-gray-800 hover:text-blue-600 dark:hover:text-blue-300'}`}>Settings</Link>
                </div>
                <div className="hidden md:flex items-center"><ThemeToggle /></div>
              </header>
              <main className="container mx-auto px-4 py-8 flex-1 w-full">
                {children}
              </main>
              <footer className="bg-white/80 dark:bg-gray-900/80 border-t border-gray-200 dark:border-gray-800 py-4 text-center text-gray-500 dark:text-gray-400 text-sm shadow-inner">
                <div className="container mx-auto px-4">
                  <p>XCA-Bot &mdash; Cryptocurrency Address Monitor</p>
                </div>
              </footer>
            </div>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
} 