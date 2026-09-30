import type { Metadata } from 'next';
import { Pixelify_Sans } from 'next/font/google';
import './globals.css';
const pixel = Pixelify_Sans({ subsets: ['latin'], weight: ['400','600','700'], variable: '--font-pixel', display: 'swap' });
export const metadata: Metadata = { title: 'priceactioner — BTC Price Action Intelligence', description: 'Live Bitcoin market data, Binance order books, sentiment and price-action scenarios for your market plan.' };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body className={pixel.variable}>{children}</body></html>;
}
