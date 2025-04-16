import { Inter } from 'next/font/google';
import './globals.css';
import ThemeClientProvider from './components/ThemeClientProvider';
import ThemeToggle from './components/ThemeToggle';
import Link from 'next/link';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'XCA-Bot Dashboard',
  description: 'XCA-Bot Cryptocurrency Address Monitor',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeClientProvider>
          <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
            <header className="sticky top-0 z-50 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
              <div className="container mx-auto px-4 py-4">
                <div className="flex justify-between items-center mb-4">
                  <h1 className="text-2xl font-bold">XCA-Bot Dashboard</h1>
                  <ThemeToggle />
                </div>
                <nav className="flex space-x-6">
                  <Link href="/" className="text-gray-600 dark:text-gray-400 hover:text-blue-500 dark:hover:text-blue-500 pb-2">Dashboard</Link>
                  <Link href="/matches" className="text-gray-600 dark:text-gray-400 hover:text-blue-500 dark:hover:text-blue-500 pb-2">Matches</Link>
                  <Link href="/settings" className="text-gray-600 dark:text-gray-400 hover:text-blue-500 dark:hover:text-blue-500 pb-2">Settings</Link>
                </nav>
              </div>
            </header>
            <main className="container mx-auto px-4 py-8">
              {children}
            </main>
            <footer className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 mt-auto py-4">
              <div className="container mx-auto px-4 text-center text-gray-600 dark:text-gray-400">
                <p>XCA-Bot - Cryptocurrency Address Monitor</p>
              </div>
            </footer>
          </div>
        </ThemeClientProvider>
      </body>
    </html>
  );
} 