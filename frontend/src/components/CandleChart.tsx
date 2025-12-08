import React, { useMemo } from 'react';
import {
    ComposedChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Cell
} from 'recharts';
import { format } from 'date-fns';

interface CandleData {
    time: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
}

interface CandleChartProps {
    data: CandleData[];
    ticker: string;
    interval: string;
}

const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        const { open, high, low, close, volume } = payload[0].payload;
        return (
            <div className="bg-card border border-border p-2 rounded shadow text-xs">
                <p className="font-semibold mb-1">{format(new Date(label), 'yyyy-MM-dd HH:mm')}</p>
                <p className="text-muted-foreground">Open: <span className="text-foreground">{open.toFixed(2)}</span></p>
                <p className="text-muted-foreground">High: <span className="text-foreground">{high.toFixed(2)}</span></p>
                <p className="text-muted-foreground">Low: <span className="text-foreground">{low.toFixed(2)}</span></p>
                <p className="text-muted-foreground">Close: <span className="text-foreground">{close.toFixed(2)}</span></p>
                <p className="text-muted-foreground">Vol: <span className="text-foreground">{volume.toLocaleString()}</span></p>
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

    if (!highVal || !lowVal || highVal === lowVal) return null;

    const pixelHeight = height;
    const valueRange = highVal - lowVal;
    if (valueRange === 0) return null;

    const pixelsPerUnit = pixelHeight / valueRange;

    const yHigh = y;
    const yLow = y + height;

    const yOpen = y + (highVal - openVal) * pixelsPerUnit;
    const yClose = y + (highVal - closeVal) * pixelsPerUnit;

    const bodyTop = Math.min(yOpen, yClose);
    const bodyHeight = Math.max(1, Math.abs(yOpen - yClose)); // Ensure at least 1px

    // Center the wick
    const wickX = x + width / 2;

    return (
        <g>
            {/* Wick */}
            <line x1={wickX} y1={yHigh} x2={wickX} y2={yLow} stroke={color} strokeWidth={1} />
            {/* Body */}
            <rect
                x={x}
                y={bodyTop}
                width={width}
                height={bodyHeight}
                fill={color}
                stroke={color} // Stroke avoids gaps
            />
        </g>
    );
};

export const CandleChart: React.FC<CandleChartProps> = ({ data, ticker, interval }) => {

    // Filter invalid data
    const validData = useMemo(() => {
        if (!data) return [];
        return data.filter(d =>
            d.open != null && d.close != null && d.high != null && d.low != null
        ).map(d => ({
            ...d,
            // Pre-calculate min/max for the Bar domain
            barMin: d.low,
            barMax: d.high
        }));
    }, [data]);

    if (!validData || validData.length === 0) {
        return <div className="h-full flex items-center justify-center text-muted-foreground bg-muted/10 rounded border border-dashed border-border p-4">No price data available</div>;
    }

    return (
        <div className="w-full h-full flex flex-col">
            <h3 className="text-sm font-semibold mb-2">Price History - {ticker} ({interval})</h3>
            <div className="flex-1 min-h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart
                        data={validData}
                        margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
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
                        />
                        <YAxis
                            domain={['auto', 'auto']}
                            stroke="hsl(var(--muted-foreground))"
                            tick={{ fontSize: 11 }}
                            tickFormatter={(val) => val.toFixed(1)}
                        />
                        <Tooltip content={<CustomTooltip />} />

                        {/* Candlestick using Custom Shape */}
                        <Bar
                            dataKey={(d) => [d.low, d.high]}
                            shape={<CandleShape />}
                            isAnimationActive={false}
                        />
                    </ComposedChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};
