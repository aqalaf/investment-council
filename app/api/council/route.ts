import {env} from 'cloudflare:workers';
import {getChatGPTUser} from '@/app/chatgpt-auth';
import {parseTickers} from '@/lib/council-types';
import {runCouncil,discoverCandidates} from '@/lib/council';
export async function POST(request:Request){
 const user=await getChatGPTUser();if(!user)return Response.json({error:'Please sign in to your private workspace.'},{status:401});
 const origin=request.headers.get('origin');if(origin&&origin!==new URL(request.url).origin)return Response.json({error:'Request origin is not allowed.'},{status:403});
 const bindings=env as unknown as Record<string,string>;
 if(!bindings.OPENAI_API_KEY)return Response.json({error:'The AI connection is not configured yet.'},{status:503});
 let tickers:string[]=[];let discover=false;
 try{const raw=await request.text();if(raw.length>1000)throw new Error('Request too large.');const body=JSON.parse(raw);discover=body.mode==='discover';if(!discover)tickers=parseTickers(typeof body.tickers==='string'?body.tickers:'');}catch(e){return Response.json({error:e instanceof Error?e.message:'Invalid symbols.'},{status:400});}
 const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),480000);
 request.signal.addEventListener('abort',()=>controller.abort(),{once:true});
 const encoder=new TextEncoder();
 const stream=new ReadableStream({async start(out){const send=(event:unknown)=>{if(!controller.signal.aborted)out.enqueue(encoder.encode(JSON.stringify(event)+'\n'));};
 try{if(discover){send({type:'status',message:'The Fundamentalist is discovering candidates across US sectors.'});tickers=await discoverCandidates(bindings.OPENAI_API_KEY,controller.signal,bindings.OPENAI_MODEL||'gpt-6-astra');}send({type:'universe',tickers});await runCouncil(bindings.OPENAI_API_KEY,tickers,send,controller.signal,bindings.OPENAI_MODEL||'gpt-6-astra');}
 catch(e){const error=e as {status?:number;code?:string;name?:string};let message='The research session could not finish. Partial analysis is not a completed recommendation.';
 if(error.status===401)message='The AI key was rejected. Reconnect the API account.';
 if(error.status===429)message=['credit_balance_exhausted','insufficient_quota'].includes(error.code||'')?'The API account has no available credits. Add credits in API billing, then start a new session.':'The AI account reached a rate limit. Wait a moment, then retry.';
 if(error.status===403||error.status===404)message='The selected AI model is not available to this API project.';
 if(controller.signal.aborted){try{out.enqueue(encoder.encode(JSON.stringify({type:'error',message:'The research session stopped or timed out. No final recommendation was issued.'})+'\n'));}catch{}}
 else send({type:'error',message});}
 finally{controller.abort();clearTimeout(timeout);try{out.close();}catch{}}},cancel(){controller.abort();clearTimeout(timeout);}});
 return new Response(stream,{headers:{'Content-Type':'application/x-ndjson','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
}
