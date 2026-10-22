import type {Metadata} from 'next';
import './globals.css';
import {Shell} from '@/components/UI';
export const metadata:Metadata={title:'FourthDown Analytics | NFL Prediction Research',description:'NFL game outcome modeling, research and performance analytics. Data-grounded educational project.'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body><Shell>{children}</Shell></body></html>}
