'use client';
import {useMemo, useState} from 'react';
import {Activity, ArrowUpRight, CalendarDays, CheckCircle2, Info, MapPin} from 'lucide-react';
import {useAPI, teamNames} from '@/lib/api';
import {Coverage, ErrorState, LoadingState, PageIntro, TeamBadge} from '@/components/UI';
import type {TrendsResponse, TrendCard} from '@/lib/types';

const names = Object.keys(teamNames).sort((a,b)=>teamNames[a].localeCompare(teamNames[b]));
const groupOrder=['Results','Offense','Defense','Venue','Consistency','Head to head','Game flow'];
function Select({label,value,onChange,options}:{label:string;value:string;onChange:(v:string)=>void;options:{value:string;label:string}[]}){
  return <label className="trend-select-label"><span>{label}</span><select className="select" value={value} onChange={e=>onChange(e.target.value)}>{options.map(x=><option key={x.value} value={x.value}>{x.label}</option>)}</select></label>;
}
function StatCard({item,expanded,onToggle,partial}:{item:TrendCard;expanded:boolean;onToggle:()=>void;partial:boolean}){
 const summary=`${item.hits} of ${item.sample}`;
 return <article className="trend-card">
  <div className="trend-card-kicker">{item.category}</div>
  <h3>{item.title}</h3>
  <div className="trend-stat"><strong>{summary}</strong><span>{Math.round(item.rate*100)}% of the sample</span></div>
  <div className="trend-mini-track" aria-label={`${item.hits} out of ${item.sample} games`}><div style={{width:`${item.rate*100}%`}}/></div>
  <p>{item.current_streak>1?`Current run in available records: ${item.current_streak} games.`:'Based on completed games only.'}</p>
  <button type="button" className="trend-detail-toggle" onClick={onToggle} aria-expanded={expanded}>{expanded?'Hide game details':'See supporting games'} <ArrowUpRight size={13}/></button>
  {expanded&&<div className="trend-proof"><div className="trend-proof-note">{partial?'Partial archive. Gaps may exist.':'Most recent games in the selected sample.'}</div>
   {item.games.map(g=>{const match=item.game_ids.includes(g.id);return <div className="trend-proof-row" key={g.id}>
    <div><span>{g.season} · W{g.week}</span><b>vs {g.opponent}</b><small>{g.venue==='home'?'Home':g.venue==='away'?'Away':'Neutral'}</small></div>
    <div><b>{g.points_for}–{g.points_against}</b><span>{match?<CheckCircle2 size={14} aria-label="matches trend"/>:'—'}</span></div>
   </div>})}
  </div>}
 </article>;
}
export default function Trends(){
 const [team,setTeam]=useState('KC'),[opponent,setOpponent]=useState(''),[venue,setVenue]=useState('all'),[last,setLast]=useState('5'),[expanded,setExpanded]=useState<string[]>([]);
 const path=`/api/trends?team=${encodeURIComponent(team)}${opponent?`&opponent=${encodeURIComponent(opponent)}`:''}&venue=${venue}&last=${last}`;
 const {data,loading,error}=useAPI<TrendsResponse>(path);
 const groups=useMemo(()=>data?groupOrder.map(name=>({name,items:data.cards.filter(x=>x.category===name)})).filter(x=>x.items.length>0):[],[data]);
 return <>
  <PageIntro eyebrow="TEAM TRENDS" title="Find the story behind the numbers." subtitle="Scoring runs, defensive patterns, home-field splits and head-to-head history—with the games to back them up."/>
  <section className="panel trend-controls"><div className="trend-controls-heading"><div><h2>Build a trend</h2><p>Choose a team and narrow the view. Every number recalculates from completed games.</p></div><Activity size={20}/></div>
  <div className="trend-filters">
   <Select label="Team" value={team} onChange={v=>{setTeam(v);if(v===opponent)setOpponent('');setExpanded([])}} options={names.map(x=>({value:x,label:teamNames[x]}))}/>
   <Select label="Opponent" value={opponent} onChange={v=>{setOpponent(v);setExpanded([])}} options={[{value:'',label:'All opponents'},...names.filter(n=>n!==team).map(n=>({value:n,label:teamNames[n]}))]}/>
   <Select label="Venue" value={venue} onChange={v=>{setVenue(v);setExpanded([])}} options={[{value:'all',label:'Any venue'},{value:'home',label:'At home'},{value:'away',label:'On the road'},{value:'neutral',label:'Neutral site'}]}/>
   <Select label="Recent games" value={last} onChange={v=>{setLast(v);setExpanded([])}} options={[3,5,8,10,15,20].map(x=>({value:String(x),label:`Last ${x}`}))}/>
  </div></section>
  {loading?<LoadingState/>:error?<ErrorState error={error}/>:data&&<>
   <Coverage partial={data.partial_coverage}/>
   <div className="trend-context"><div className="trend-current-team"><TeamBadge team={team} size="large"/><div><h2>{teamNames[team]}</h2><p>{opponent?`Against ${teamNames[opponent]}`:'Against all opponents'} · {venue==='all'?'All venues':venue==='home'?'Home games':venue==='away'?'Away games':'Neutral-site games'}</p></div></div>
   <span>{data.sample_games} of {last} requested games found</span></div>
   {data.averages&&<div className="trend-summary-grid">
    <div><span>Points scored / game</span><strong>{data.averages.points_for.toFixed(1)}</strong></div>
    <div><span>Points allowed / game</span><strong>{data.averages.points_against.toFixed(1)}</strong></div>
    <div><span>Average scoring margin</span><strong>{data.averages.point_margin>0?'+':''}{data.averages.point_margin.toFixed(1)}</strong></div>
   </div>}
   <div className="trend-editorial-note"><Info size={17}/><span>These are descriptive patterns, not extra evidence that a team will win its next game. {data.coverage_note} Every trend includes its denominator and supporting games.</span></div>
   {groups.length?groups.map(group=><section className="trend-section" key={group.name}><div className="section-head"><div><h2>{group.name}</h2><p>Observed patterns from {data.sample_games} or fewer relevant completed games.</p></div></div>
    <div className="trend-card-grid">{group.items.map(item=><StatCard item={item} key={item.id} partial={data.partial_coverage} expanded={expanded.includes(item.id)} onToggle={()=>setExpanded(p=>p.includes(item.id)?p.filter(x=>x!==item.id):[...p,item.id])}/>)}</div>
   </section>):<div className="trend-no-data"><CalendarDays size={24}/><h2>Not enough completed games for a defensible trend</h2><p>This filter has only {data.sample_games} verified game{data.sample_games===1?'':'s'}. Try all venues, a different opponent, or refresh the full nflverse dataset.</p></div>}
   <section className="panel"><div className="section-head"><div><h2>Games in this sample</h2><p>Most recent first, with the selected venue and opponent filters applied.</p></div><MapPin size={18}/></div><div className="table-scroll"><table className="data-table"><thead><tr><th>SEASON / WEEK</th><th>OPPONENT</th><th>VENUE</th><th>SCORE</th><th>RESULT</th></tr></thead><tbody>{data.recent_games.map(g=><tr key={g.id}><td>{g.season} · {g.week}</td><td>{teamNames[g.opponent]||g.opponent}</td><td>{g.venue}</td><td>{g.points_for}–{g.points_against}</td><td>{g.tie?'Tie':g.win?'Win':'Loss'}</td></tr>)}</tbody></table>{!data.recent_games.length&&<div className="empty-state">No completed games found for these filters.</div>}</div></section>
  </>}
 </>;
}
