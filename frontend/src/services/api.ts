import { Capacitor } from '@capacitor/core';
export type Media={reference:string;title:string;thumbnail:string|null;duration:number|null;qualities:{id:string;label:string;height:number|null}[]};
export type Job={id:string;token?:string;title:string;quality:string;status:string;percent:number|null;downloaded_bytes:number;total_bytes:number|null;speed:number|null;error:string|null;expires_at:number};
export const native=Capacitor.isNativePlatform();
export function baseUrl(){return(localStorage.getItem('server')||import.meta.env.VITE_API_URL||'').replace(/\/$/,'');}
export function saveServer(value:string){if(value){const u=new URL(value);if(u.protocol!=='https:'||u.username||u.password||u.pathname!=='/'||u.search||u.hash)throw Error('Use an HTTPS server address without a path.');}localStorage.setItem('server',value.replace(/\/$/,''));}
export async function api<T>(path:string,options:RequestInit={}):Promise<T>{
 if(native&&!baseUrl())throw Error('Connect your download server in Settings first.');
 const r=await fetch(`${baseUrl()}/api/v1${path}`,{...options,headers:{'Content-Type':'application/json',...options.headers},signal:options.signal??AbortSignal.timeout(200000)});
 if(!r.ok){const b=await r.json().catch(()=>({}));throw Error(b.error?.message||b.detail?.[0]?.msg||`Request failed (${r.status}). Please try again.`);}
 return r.status===204?undefined as T:r.json();
}
export async function watchJob(job:Job,token:string,signal:AbortSignal,update:(j:Job)=>void){
 const r=await fetch(`${baseUrl()}/api/v1/downloads/${job.id}/events`,{headers:{Authorization:`Bearer ${token}`},signal});
 if(!r.ok||!r.body)throw Error('Progress disconnected. Tap Refresh to check your download.');
 const reader=r.body.getReader(),decoder=new TextDecoder();let pending='';
 try{while(true){const{done,value}=await reader.read();if(done)break;pending+=decoder.decode(value,{stream:true});let split;while((split=pending.indexOf('\n\n'))!==-1){const block=pending.slice(0,split);pending=pending.slice(split+2);const data=block.split('\n').find(l=>l.startsWith('data: '));if(data)update(JSON.parse(data.slice(6)));}}}finally{reader.releaseLock();}
}
