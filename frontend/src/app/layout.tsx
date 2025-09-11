import './globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { PlayerModal } from '@/components/player/PlayerModal';
import { NotificationToast } from '@/components/ui/NotificationToast';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Fantasy Football Dashboard',
  description: 'Comprehensive fantasy football data aggregation and analysis',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>
        <div className="min-h-screen bg-dark-900 text-white">
          <Header />
          <div className="flex">
            <Sidebar />
            <main className="flex-1 md:ml-0">
              {children}
            </main>
          </div>
          <PlayerModal />
          <NotificationToast />
        </div>
      </body>
    </html>
  );
}