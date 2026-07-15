import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'OBE03 Manufacturing Pipeline',
  description: 'Lecture 3 and Lecture 4 data science pipeline lab'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
