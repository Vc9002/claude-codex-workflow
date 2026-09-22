import { PolymarketUS } from 'polymarket-us';
import fs from 'fs';
function envFrom(p){const o={};if(!fs.existsSync(p))return o;for(const l of fs.readFileSync(p,'utf8').split('\n')){const m=l.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/i);if(!m)continue;let v=m[2].trim();if((v.startsWith('"')&&v.endsWith('"'))||(v.startsWith("'")&&v.endsWith("'")))v=v.slice(1,-1);o[m[1]]=v;}return o;}
const sdkDir=process.argv[2]; const outFile=process.argv[3];
const e=envFrom(sdkDir+'/.env');
const client=new PolymarketUS({keyId:e.POLYMARKET_KEY_ID,secretKey:e.POLYMARKET_SECRET_KEY});
const out={pulledAt:new Date().toISOString(),activities:[]};
out.balances=await client.account.balances();
out.positions=await client.portfolio.positions();
let cursor,pages=0;
while(true){const r=await client.portfolio.activities({limit:100,cursor,sortOrder:'SORT_ORDER_ASCENDING'});const a=r.activities||[];out.activities.push(...a);pages++;if(r.eof||!r.nextCursor||a.length===0)break;cursor=r.nextCursor;if(pages>500)break;}
fs.writeFileSync(outFile,JSON.stringify(out));
console.error('poly pulled',out.activities.length,'activities, balance',out.balances.balances[0].currentBalance);
