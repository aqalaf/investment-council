import {env} from 'cloudflare:workers';
import {getChatGPTUser} from '@/app/chatgpt-auth';
export async function GET(){if(!await getChatGPTUser())return Response.json({ready:false,signedIn:false},{status:401});return Response.json({signedIn:true,ready:!!(env as unknown as Record<string,string>).OPENAI_API_KEY},{headers:{'Cache-Control':'no-store'}});}
