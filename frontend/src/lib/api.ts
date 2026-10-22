'use client';
import {useEffect,useState} from 'react';
const BASE=process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
export async function getJSON<T>(path:string):Promise<T>{
  const r=await fetch(`${BASE}${path}`,{cache:'no-store'});
  if(!r.ok){let reason='';try{const p=await r.json();reason=typeof p.detail==='string'?p.detail:''}catch{}throw new Error(reason||`API request failed (${r.status})`)}
  return r.json() as Promise<T>;
}
export function useAPI<T>(path:string){
  const [data,setData]=useState<T|null>(null);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState<string|null>(null);
  useEffect(()=>{let alive=true;setLoading(true);setError(null);getJSON<T>(path).then(v=>{if(alive)setData(v)}).catch(e=>{if(alive)setError(e.message)}).finally(()=>{if(alive)setLoading(false)});return()=>{alive=false}},[path]);
  return {data,loading,error};
}
export const pct=(n:number)=>`${(n*100).toFixed(1)}%`;
export const signed=(n:number)=>`${n>0?'+':''}${n.toFixed(1)}`;
export const teamNames:Record<string,string>={ARI:'Arizona Cardinals',ATL:'Atlanta Falcons',BAL:'Baltimore Ravens',BUF:'Buffalo Bills',CAR:'Carolina Panthers',CHI:'Chicago Bears',CIN:'Cincinnati Bengals',CLE:'Cleveland Browns',DAL:'Dallas Cowboys',DEN:'Denver Broncos',DET:'Detroit Lions',GB:'Green Bay Packers',HOU:'Houston Texans',IND:'Indianapolis Colts',JAX:'Jacksonville Jaguars',KC:'Kansas City Chiefs',LV:'Las Vegas Raiders',LAC:'Los Angeles Chargers',LA:'Los Angeles Rams',MIA:'Miami Dolphins',MIN:'Minnesota Vikings',NE:'New England Patriots',NO:'New Orleans Saints',NYG:'New York Giants',NYJ:'New York Jets',PHI:'Philadelphia Eagles',PIT:'Pittsburgh Steelers',SF:'San Francisco 49ers',SEA:'Seattle Seahawks',TB:'Tampa Bay Buccaneers',TEN:'Tennessee Titans',WAS:'Washington Commanders'};
