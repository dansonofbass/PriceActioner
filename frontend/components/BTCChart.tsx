'use client';
import { useEffect, useRef } from 'react';
import { createChart, CandlestickSeries, HistogramSeries, ColorType, type Time, type TickMarkType, type UTCTimestamp, type IChartApi, type ISeriesApi } from 'lightweight-charts';
import { localChartTime, localChartTick } from '@/lib/chart-time';
import type { Candle, Zone } from '@/lib/types';
const EMPTY_ZONES:Zone[]=[];
export default function BTCChart({ candles, zones = EMPTY_ZONES }: { candles: Candle[]; zones?: Zone[] }) {
 const container=useRef<HTMLDivElement>(null);
 const chartRef=useRef<IChartApi|null>(null);
 const priceRef=useRef<ISeriesApi<'Candlestick'>|null>(null);
 const volumeRef=useRef<ISeriesApi<'Histogram'>|null>(null);
 const fitted=useRef(false);
 useEffect(()=>{
  if(!container.current)return;
  const chart=createChart(container.current,{autoSize:true,
   layout:{background:{type:ColorType.Solid,color:'#f1f1f1'},textColor:'#252525',fontFamily:'Pixelify Sans, monospace',fontSize:12,attributionLogo:true},
   localization:{locale:'en-GB',timeFormatter:(time:Time)=>localChartTime(time)},
   grid:{vertLines:{color:'#dedede'},horzLines:{color:'#dedede'}},rightPriceScale:{borderColor:'#080808'},
   timeScale:{borderColor:'#080808',timeVisible:true,tickMarkFormatter:(time:Time,kind:TickMarkType)=>localChartTick(time,kind)},
   crosshair:{vertLine:{color:'#2f6efa'},horzLine:{color:'#2f6efa'}}});
  const price=chart.addSeries(CandlestickSeries,{upColor:'#f1f1f1',downColor:'#252525',borderUpColor:'#080808',borderDownColor:'#080808',wickUpColor:'#080808',wickDownColor:'#080808'});
  const volume=chart.addSeries(HistogramSeries,{priceFormat:{type:'volume'},priceScaleId:'volume'});
  volume.priceScale().applyOptions({scaleMargins:{top:.83,bottom:0}});
  price.priceScale().applyOptions({scaleMargins:{top:.08,bottom:.23}});
  chartRef.current=chart;priceRef.current=price;volumeRef.current=volume;fitted.current=false;
  return()=>{chart.remove();chartRef.current=null;priceRef.current=null;volumeRef.current=null;};
 },[]);
 useEffect(()=>{
  if(!chartRef.current||!priceRef.current||!volumeRef.current)return;
  priceRef.current.setData(candles.map(c=>({time:Math.floor(c.timestamp/1000) as UTCTimestamp,open:c.open,high:c.high,low:c.low,close:c.close})));
  volumeRef.current.setData(candles.map(c=>({time:Math.floor(c.timestamp/1000) as UTCTimestamp,value:c.volume,color:'#b8b8b8'})));
  if(!fitted.current&&candles.length){chartRef.current.timeScale().fitContent();if(candles.length>90)chartRef.current.timeScale().setVisibleLogicalRange({from:candles.length-90,to:candles.length+3});fitted.current=true;}
 },[candles]);
 useEffect(()=>{
  const price=priceRef.current;if(!price)return;
  const lines=zones.map(z=>price.createPriceLine({price:z.midpoint,color:'#2f6efa',lineWidth:1,lineStyle:2,axisLabelVisible:true,title:z.zone_type.toUpperCase()}));
  return()=>{if(priceRef.current===price)lines.forEach(line=>price.removePriceLine(line));};
 },[zones]);
 return <div ref={container} className="candle-chart" role="img" aria-label={`BTC candlestick chart with ${candles.length} candles and volume. Times are shown in your device timezone.`}/>;
}
