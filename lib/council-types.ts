export const analysts = [
 {id:"quality",name:"The Fundamentalist",specialty:"BUSINESS QUALITY",color:"blue",detail:"Finds durable advantages, healthy cash flow, and room to compound."},
 {id:"value",name:"The Valuer",specialty:"PRICE & PATIENCE",color:"lime",detail:"Tests what the price assumes and where a margin of safety exists."},
 {id:"risk",name:"The Skeptic",specialty:"RISK & RESILIENCE",color:"orange",detail:"Challenges the thesis, stress-tests the downside, and keeps dissent visible."},
] as const;
export type AnalystId = typeof analysts[number]["id"];
export type Verdict = "candidate"|"watch"|"avoid"|"insufficient";
export type Source = {url:string;title:string};
export type View = {ticker:string;company:string;verdict:Verdict;thesis:string;concern:string;changeMind:string;evidenceUrls:string[];quote:number|null;quoteDate:string|null;quoteSourceUrl:string|null;fairLow:number|null;fairHigh:number|null;valuationAssumptions:string;seriousRisk:boolean};
export type Ballot = {analyst:AnalystId;challenge:string;response:string;views:View[]};
export type Research = {analyst:AnalystId;text:string;sources:Source[]};
export type Decision = {ticker:string;company:string;verdict:Verdict;support:number;reason:string;views:(View & {analyst:AnalystId})[]};
export type Report = {createdAt:string;tickers:string[];research:Research[];ballots:Ballot[];decisions:Decision[];model:string};
export type Event = {type:"universe";tickers:string[]}|{type:"status";message:string;analyst?:AnalystId}|{type:"research";data:Research}|{type:"ballot";data:Ballot}|{type:"complete";data:Report}|{type:"error";message:string};
export const labels:Record<Verdict,string>={candidate:"Research further",watch:"Watch",avoid:"Pass",insufficient:"Insufficient evidence"};
export function parseTickers(raw:string){const ts=[...new Set(raw.toUpperCase().split(/[\s,;]+/).filter(Boolean))];if(ts.length<1||ts.length>8||ts.some(t=>! /^[A-Z]{1,5}(?:[.-][A-Z])?$/.test(t)))throw new Error("Enter 1–8 US stock symbols, separated by commas (for example: MSFT, V, BRK.B).");return ts;}
export function combine(tickers:string[],ballots:Ballot[],date=new Date()):Decision[]{return tickers.map(ticker=>{
 const views=ballots.flatMap(b=>b.views.filter(v=>v.ticker===ticker).map(v=>({...v,analyst:b.analyst})));
 const risk=views.find(v=>v.analyst==='risk');const value=views.find(v=>v.analyst==='value');
 const support=views.filter(v=>v.verdict==='candidate').length;
 const quoteTime=value?.quoteDate?Date.parse(value.quoteDate):NaN;
 const fresh=Number.isFinite(quoteTime)&&quoteTime<=date.getTime()&&date.getTime()-quoteTime<=7*86400000&&!!value?.quote&&!!value?.quoteSourceUrl;
 const missing=views.length!==3||views.some(v=>v.evidenceUrls.length===0||v.verdict==='insufficient')||!fresh;
 let verdict:Verdict='watch',reason='The council has unresolved reservations. Read the dissent before considering an investment.';
 if(risk?.seriousRisk||risk?.verdict==='avoid'){verdict='avoid';reason='The risk analyst found a material objection to this investment.';}
 else if(missing){verdict='insufficient';reason='A complete sourced assessment and a dated price from the last seven days are required.';}
 else if(views.filter(v=>v.verdict==='avoid').length>=2){verdict='avoid';reason='At least two analysts oppose the investment case.';}
 else if(support===3){verdict='candidate';reason='All three analysts support further research; this is agreement, not a probability of success.';}
 return {ticker,company:views[0]?.company||ticker,verdict,support,reason,views};
 }).sort((a,b)=>({candidate:0,watch:1,insufficient:2,avoid:3}[a.verdict]-{candidate:0,watch:1,insufficient:2,avoid:3}[b.verdict]));}
