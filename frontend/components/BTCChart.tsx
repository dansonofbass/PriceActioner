'use client';
import { useEffect, useRef } from 'react';
import { createChart, CandlestickSeries, HistogramSeries, ColorType, type UTCTimestamp } from 'lightweight-charts';
import type { Candle, Zone } from '@/lib/types';
export default function BTCChart({ candles, zones = [] }: { candles: Candle[]; zones?: Zone[] }) {
 const ref=useRef<HTMLDivElement>(null);
 useEffect(()=>{if(!ref.current)return;const chart=createChart(ref.current,{autoSize:true,layout:{background:{type:ColorType.Solid,color:'#f1f1f1'},textColor:'#252525',fontFamily:'Pixelify Sans, monospace',fontSize:12,attributionLogo:true},grid:{vertLines:{color:'#dedede'},horzLines:{color:'#dedede'}},rightPriceScale:{borderColor:'#080808'},timeScale:{borderColor:'#080808',timeVisible:true},crosshair:{vertLine:{color:'#2f6efa'},horzLine:{color:'#2f6efa'}}});
 const series=chart.addSeries(CandlestickSeries,{upColor:'#f1f1f1',downColor:'#252525',borderUpColor:'#080808',borderDownColor:'#080808',wickUpColor:'#080808',wickDownColor:'#080808'});
 series.setData(candles.map(c=>({time:Math.floor(c.timestamp/1000) as UTCTimestamp,open:c.open,high:c.high,low:c.low,close:c.close})));
 const volume=chart.addSeries(HistogramSeries,{priceFormat:{type:'volume'},priceScaleId:'volume'});volume.priceScale().applyOptions({scaleMargins:{top:.83,bottom:0}});volume.setData(candles.map(c=>({time:Math.floor(c.timestamp/1000) as UTCTimestamp,value:c.volume,color:'#b8b8b8'})));series.priceScale().applyOptions({scaleMargins:{top:.08,bottom:.23}});
 zones.forEach(z=>series.createPriceLine({price:z.midpoint,color:'#2f6efa',lineWidth:1,lineStyle:2,axisLabelVisible:true,title:z.zone_type.toUpperCase()}));chart.timeScale().fitContent();if(candles.length>90)chart.timeScale().setVisibleLogicalRange({from:candles.length-90,to:candles.length+3});return()=>chart.remove();},[candles,zones]);
 return <div ref={ref} className="candle-chart" role="img" aria-label={`BTC candlestick chart with ${candles.length} candles and volume. Detailed values are available in the admin raw data table.`}/>;
}
