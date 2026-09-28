import type { Time } from 'lightweight-charts';

function dateOf(time: Time): Date {
 if(typeof time==='number')return new Date(time*1000);
 if(typeof time==='string')return new Date(time+'T00:00:00Z');
 return new Date(Date.UTC(time.year,time.month-1,time.day));
}
export function localChartTime(time:Time, timeZone?:string):string {
 return new Intl.DateTimeFormat('en-GB',{timeZone,year:'numeric',month:'short',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(dateOf(time));
}
export function localChartTick(time:Time, kind:number, timeZone?:string):string {
 const options:Intl.DateTimeFormatOptions={timeZone,hourCycle:'h23'};
 if(kind===0)options.year='numeric';
 else if(kind===1)options.month='short';
 else if(kind===2){options.day='2-digit';options.month='short';}
 else {options.hour='2-digit';options.minute='2-digit';if(kind===4)options.second='2-digit';}
 return new Intl.DateTimeFormat('en-GB',options).format(dateOf(time));
}
