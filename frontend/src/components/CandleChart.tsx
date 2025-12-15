import React, { useMemo } from 'react';
import {
    ComposedChart,
    Bar,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    Scatter,
    ReferenceLine
} from 'recharts';
import { format } from 'date-fns';

interface CandleData {
    time: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    cd_signal?: boolean;
    mc_signal?: boolean;
    ema_13?: number;
    ema_21?: number;
    ema_144?: number;
    ema_169?: number;
}

interface CandleChartProps {
    data: CandleData[];
    ticker: string;
    interval: string;
}

const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        // Find the main payload item (usually the candle or volume, we want all info)
        // payload[0] might be volume or candle depending on order/hover
        // But we can extract from payload[0].payload which is the full data object
        const { open, high, low, close, volume, cd_signal, mc_signal } = payload[0].payload;

        return (
            <div className="bg-card border border-border p-2 rounded shadow text-xs z-50">
                <p className="font-semibold mb-1">{format(new Date(label), 'yyyy-MM-dd HH:mm')}</p>
                <div className="grid grid-cols-2 gap-x-4">
                    <span className="text-muted-foreground">Open:</span> <span className="text-foreground text-right">{open.toFixed(2)}</span>
                    <span className="text-muted-foreground">High:</span> <span className="text-foreground text-right">{high.toFixed(2)}</span>
                    <span className="text-muted-foreground">Low:</span> <span className="text-foreground text-right">{low.toFixed(2)}</span>
                    <span className="text-muted-foreground">Close:</span> <span className="text-foreground text-right">{close.toFixed(2)}</span>
                    <span className="text-muted-foreground">Vol:</span> <span className="text-foreground text-right">{volume.toLocaleString()}</span>
                </div>
                {(cd_signal || mc_signal) && (
                    <div className="mt-2 pt-2 border-t border-border flex flex-col gap-1">
                        {cd_signal && <span className="text-green-500 font-bold flex items-center gap-1">↑ CD BUY</span>}
                        {mc_signal && <span className="text-red-500 font-bold flex items-center gap-1">↓ MC SELL</span>}
                    </div>
                )}
            </div>
        );
    }
    return null;
};

const CandleShape = (props: any) => {
    const { x, y, width, height } = props;
    const { payload } = props;
    const { open: openVal, close: closeVal, high: highVal, low: lowVal } = payload;

    const isUp = closeVal >= openVal;
    const color = isUp ? '#22c55e' : '#ef4444';

    if (highVal === undefined || lowVal === undefined) return null;

    // Y Axis is inverted (0 is top), but values are normal
    // We need to map values to pixels. 
    // Recharts passes us x,y,width,height which is the bar's bounding box.
    // However, for candlestick, we need exact scaling.
    // IMPORTANT: The 'Bar' component with dataKey={[min, max]} will calculate y and height 
    // corresponding to 'min' and 'max' scaled to the axis.
    // So 'y' is the top (max price), 'height' is the span (max - min).
    // We can assume strict linear scaling within this box.

    // BUT we need open/close pixel positions.
    // height = (max - min) * scale
    // scale = height / (max - min)

    const range = highVal - lowVal;
    const scale = range === 0 ? 0 : height / range;

    // y is the pixel position of the TOP (highVal)
    // We calculate offsets from top (highVal)

    const openOffset = (highVal - openVal) * scale;
    const closeOffset = (highVal - closeVal) * scale;

    const bodyTop = Math.min(openOffset, closeOffset);
    const bodyHeight = Math.max(1, Math.abs(openOffset - closeOffset));

    // Center wick
    const wickX = x + width / 2;

    return (
        <g>
            <line x1={wickX} y1={y} x2={wickX} y2={y + height} stroke={color} strokeWidth={1} />
            <rect
                x={x}
                y={y + bodyTop}
                width={width}
                height={bodyHeight}
                fill={color}
                stroke={color}
            />
        </g>
    );
};

export const CandleChart: React.FC<CandleChartProps> = ({ data, ticker, interval }) => {

    const validData = useMemo(() => {
        if (!data) return [];
        return data.filter(d =>
            d.open != null && d.close != null && d.high != null && d.low != null
        ).map(d => ({
            ...d,
            // Prepare signals for scatter plots
            // We'll place signals slightly above high (sell) or below low (buy)
            buySignal: d.cd_signal ? d.low * 0.999 : null,
            sellSignal: d.mc_signal ? d.high * 1.001 : null
        }));
    }, [data]);

    if (!validData || validData.length === 0) {
        return <div className="h-full flex items-center justify-center text-muted-foreground bg-muted/10 rounded border border-dashed border-border p-4">No price data available</div>;
    }

    return (
        <div className="w-full h-full flex flex-col">
            <h3 className="text-sm font-semibold mb-2">Price History - {ticker} ({interval})</h3>

            {/* Price Chart - Top Section */}
            <div className="flex-1 min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart
                        data={validData}
                        syncId="candleGraph"
                        margin={{ top: 10, right: 30, left: 10, bottom: 0 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" opacity={0.5} />

                        <XAxis
                            dataKey="time"
                            tickFormatter={(tick) => {
                                try {
                                    return format(new Date(tick), 'MM-dd')
                                } catch (e) {
                                    return tick;
                                }
                            }}
                            stroke="hsl(var(--muted-foreground))"
                            tick={{ fontSize: 11 }}
                            minTickGap={30}
                            hide // Hide XAxis on top chart to avoid clutter, user can see specific time in tooltip
                        />

                        <YAxis
                            domain={['auto', 'auto']}
                            stroke="hsl(var(--muted-foreground))"
                            tick={{ fontSize: 11 }}
                            tickFormatter={(val: number) => val.toFixed(1)}
                            scale="linear"
                            label={{ value: 'Price', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle' }, fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                        />

                        <Tooltip content={<CustomTooltip />} />
                        <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} align="center" />

                        {/* Candlestick - Using [low, high] with custom shape */}
                        <Bar
                            name="Price"
                            dataKey={(d) => [d.low, d.high]}
                            shape={<CandleShape />}
                            isAnimationActive={false}
                            legendType="none" // Hide generic Candle bar from legend if preferred, or keep
                        />

                        {/* Vegas Channel */}
                        <Line type="monotone" dataKey="ema_13" stroke="#0ea5e9" strokeWidth={1} dot={false} name="EMA 13" />
                        <Line type="monotone" dataKey="ema_21" stroke="#3b82f6" strokeWidth={1} dot={false} name="EMA 21" />
                        <Line type="monotone" dataKey="ema_144" stroke="#ef4444" strokeWidth={1} dot={false} name="EMA 144" />
                        <Line type="monotone" dataKey="ema_169" stroke="#f97316" strokeWidth={1} dot={false} name="EMA 169" />

                        {/* Current Price Line */}
                        <ReferenceLine
                            y={data[data.length - 1]?.close}
                            stroke="hsl(var(--foreground))"
                            strokeDasharray="3 3"
                            label={{
                                value: data[data.length - 1]?.close?.toFixed(2),
                                position: 'right',
                                fill: 'hsl(var(--foreground))',
                                fontSize: 11
                            }}
                        />

                        {/* Buy Signals (CD) */}
                        <Scatter
                            name="CD Buy Signal"
                            dataKey="buySignal"
                            shape={(props: any) => {
                                const { cx, cy } = props;
                                if (!cx || !cy) return <g />;
                                return (
                                    <path
                                        d={`M${cx},${cy} l-4,6 l8,0 z`}
                                        fill="#22c55e"
                                        stroke="#22c55e"
                                        transform={`translate(0, 10)`} // Offset below
                                    />
                                );
                            }}
                            isAnimationActive={false}
                            fill="#22c55e"
                        />

                        {/* Sell Signals (MC) */}
                        <Scatter
                            name="MC Sell Signal"
                            dataKey="sellSignal"
                            shape={(props: any) => {
                                const { cx, cy } = props;
                                if (!cx || !cy) return <g />;
                                return (
                                    <path
                                        d={`M${cx},${cy} l-4,-6 l8,0 z`}
                                        fill="#ef4444"
                                        stroke="#ef4444"
                                        transform={`translate(0, -10)`} // Offset above
                                    />
                                );
                            }}
                            isAnimationActive={false}
                            fill="#ef4444"
                        />
                    </ComposedChart>
                </ResponsiveContainer>
            </div>

            {/* Volume Chart - Bottom Section */}
            <div className="h-[100px] mt-2">
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart
                        data={validData}
                        syncId="candleGraph"
                        margin={{ top: 0, right: 30, left: 10, bottom: 20 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" opacity={0.5} />

                        <XAxis
                            dataKey="time"
                            tickFormatter={(tick) => {
                                try {
                                    return format(new Date(tick), 'MM-dd')
                                } catch (e) {
                                    return tick;
                                }
                            }}
                            stroke="hsl(var(--muted-foreground))"
                            tick={{ fontSize: 11 }}
                            minTickGap={30}
                            label={{ value: 'Date', position: 'insideBottom', offset: -10, fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                        />

                        <YAxis
                            domain={[0, 'auto']}
                            stroke="hsl(var(--muted-foreground))"
                            tick={{ fontSize: 11 }}
                            tickFormatter={(val: number) => (val / 1000).toFixed(0) + 'k'}
                            label={{ value: 'Vol', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle' }, fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                        />

                        <Tooltip content={<CustomTooltip />} />

                        <Bar
                            dataKey="volume"
                            fill="hsl(var(--muted-foreground))"
                            opacity={0.5}
                            barSize={30}
                            name="Volume"
                            isAnimationActive={false}
                        />
                    </ComposedChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};
