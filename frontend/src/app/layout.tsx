import type {Metadata} from 'next';
import './globals.css';
import {Shell} from '@/components/UI';

export const metadata:Metadata={
 title:'FourthDown Analytics — Created by Aarit Thusu',
 description:'FourthDown Analytics is an independent NFL prediction and football research platform created and developed by Aarit Thusu. Historical trends, matchups and measured model results.',
 authors:[{name:'Aarit Thusu'}],
 creator:'Aarit Thusu',
 openGraph:{
  title:'FourthDown Analytics | Aarit Thusu',
  description:'Independent NFL predictions, football trends and statistical research. Created by Aarit Thusu.',
  type:'website',
 },
};
export default function RootLayout({children}:{children:React.ReactNode}){
 return <html lang="en"><body><Shell>{children}</Shell></body></html>;
}
