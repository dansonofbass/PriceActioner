export function visitorTime(timestamp:number,timeZone=Intl.DateTimeFormat().resolvedOptions().timeZone) {
 const time=new Intl.DateTimeFormat('en-GB',{timeZone,hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23',timeZoneName:'shortOffset'}).format(new Date(timestamp));
 return {time,timeZone,label:`YOUR TIME ${time} · ${timeZone}`};
}
