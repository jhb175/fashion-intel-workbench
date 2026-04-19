import type { Metadata } from 'next';
import { Inter, Noto_Sans_SC } from 'next/font/google';
import '@/styles/globals.css';
import AuthGuard from '@/components/layout/AuthGuard';
import AppLayout from '@/components/layout/AppLayout';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter', display: 'swap' });
const noto = Noto_Sans_SC({ subsets: ['latin'], weight: ['400','500','700'], variable: '--font-noto-sans-sc', display: 'swap' });

export const metadata: Metadata = { title: '潮流情报工作台', description: '全球时尚潮流资讯 AI 情报平台' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className={`${inter.variable} ${noto.variable}`}>
      <body className="font-sans min-h-screen"><AuthGuard><AppLayout>{children}</AppLayout></AuthGuard></body>
    </html>
  );
}
