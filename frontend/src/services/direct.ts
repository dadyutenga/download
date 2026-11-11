import {registerPlugin} from '@capacitor/core';
export type DirectMedia={title:string;qualities:{id:string;label:string}[]};
export type DirectStatus={status:number;bytes:number;total:number};
export const DirectVideo=registerPlugin<{
 analyze(options:{id:string;token:string}):Promise<DirectMedia>;
 download(options:{format:string}):Promise<{id:string}>;
 status(options:{id:string}):Promise<DirectStatus>;
 cancel(options:{id:string}):Promise<void>;
}>('DirectVideo');
export function postRequest(value:string){
 const u=new URL(value),match=u.pathname.match(/^\/(?:[A-Za-z0-9_]+\/status|i\/web\/status)\/([0-9]{1,25})\/?$/);
 if(u.protocol!=='https:'||!['x.com','www.x.com','twitter.com','www.twitter.com','mobile.twitter.com'].includes(u.hostname)||u.username||u.password||u.port||!match)throw Error('Paste an HTTPS link to a public X or Twitter post.');
 const id=match[1];return {id,token:((Number(id)/1e15)*Math.PI).toString(36).replace(/(0+|\.)/g,'')};
}
