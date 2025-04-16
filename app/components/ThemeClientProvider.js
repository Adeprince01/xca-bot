'use client';

import { ThemeProvider } from '../context/ThemeContext';

export default function ThemeClientProvider({ children }) {
  return <ThemeProvider>{children}</ThemeProvider>;
} 