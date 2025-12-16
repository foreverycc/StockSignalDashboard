import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
    ComposedChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    ReferenceLine,
    Line
} from 'recharts';
import { analysisApi } from '../services/api';
import { cn } from '../utils/cn';
import { formatNumberShort } from '../utils/chartUtils';

interface OptionOIChartProps {
    ticker: string;
}

export const OptionOIChart: React.FC<OptionOIChartProps> = ({ ticker }) => {
    const [selectedTimeframe, setSelectedTimeframe] = useState<'nearest' | 'week' | 'month'>('nearest');
    const [showFullRange, setShowFullRange] = useState(false);

    // Fetch options data
    const { data: optionsData, isLoading, error } = useQuery({
        queryKey: ['options', ticker],
        queryFn: () => analysisApi.getOptions(ticker),
        staleTime: 1000 * 60 * 5, // 5 minutes
        enabled: !!ticker
    });

    const activeData = useMemo(() => {
        if (!optionsData || !optionsData[selectedTimeframe]) return null;
        return optionsData[selectedTimeframe];
    }, [optionsData, selectedTimeframe]);

    const chartData = useMemo(() => {
        if (!activeData?.data) return [];
        let data = activeData.data;
        const currentPrice = optionsData?.current_price;

        if (!showFullRange && currentPrice && data.length > 0) {
            // Filter to +/- 25% of current price (50% range)
            const lowerBound = currentPrice * 0.75;
            const upperBound = currentPrice * 1.25;
            data = data.filter((d: any) => d.strike >= lowerBound && d.strike <= upperBound);
        }
        return data;
    }, [activeData, optionsData, showFullRange]);

    const expiryDate = activeData?.date || '';
    const maxPain = activeData?.max_pain;
    const currentPrice = optionsData?.current_price;

    if (isLoading) {
        return <div className="h-[350px] flex items-center justify-center text-muted-foreground">Loading option data...</div>;
    }

    if (error) {
        return (
            <div className="h-[350px] flex items-center justify-center text-red-500">
                Failed to load option data
            </div>
        );
    }

    if (!activeData || chartData.length === 0) {
        return (
            <div className="h-[350px] flex items-center justify-center text-muted-foreground">
                No option data available for this timeframe
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full space-y-4">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-2">
                <div>
                    <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                        Open Interest (Exp: {expiryDate})
                        {maxPain !== undefined && maxPain !== null && (
                            <span className="text-xs font-normal text-muted-foreground bg-muted/30 px-2 py-0.5 rounded ml-2">
                                Max Pain: {maxPain}
                            </span>
                        )}
                    </h3>
                </div>

                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setShowFullRange(!showFullRange)}
                        className={cn(
                            "px-2 py-1 text-xs font-medium rounded-md border border-border transition-colors",
                            !showFullRange ? "bg-primary/10 text-primary border-primary/20" : "text-muted-foreground hover:bg-muted"
                        )}
                        title="Show focused range around current price"
                    >
                        {showFullRange ? "Show Focused Range" : "Show All Strikes"}
                    </button>

                    <div className="flex bg-muted/20 rounded-lg p-1">
                        {(['nearest', 'week', 'month'] as const).map((tf) => (
                            <button
                                key={tf}
                                onClick={() => setSelectedTimeframe(tf)}
                                className={cn(
                                    "px-3 py-1 text-xs font-medium rounded-md transition-all",
                                    selectedTimeframe === tf
                                        ? "bg-background shadow-sm text-foreground"
                                        : "text-muted-foreground hover:text-foreground"
                                )}
                            >
                                {tf.charAt(0).toUpperCase() + tf.slice(1)}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            <div className="flex-1 min-h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart
                        data={chartData}
                        margin={{ top: 20, right: 25, left: 20, bottom: 30 }}
                        barGap={0}
                    >
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                        <XAxis
                            dataKey="strike"
                            tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                            tickLine={true}
                            axisLine={true}
                            type="number"
                            domain={['dataMin', 'dataMax']}
                        />
                        <YAxis
                            yAxisId="left"
                            tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                            tickLine={true}
                            axisLine={true}
                            tickFormatter={(value) => formatNumberShort(value)}
                        />
                        <YAxis
                            yAxisId="right"
                            orientation="right"
                            tick={{ fill: '#3b82f6', fontSize: 11 }}
                            tickLine={{ stroke: '#3b82f6' }}
                            axisLine={{ stroke: '#3b82f6' }}
                            tickFormatter={(value) => formatNumberShort(value)}
                            label={{ value: 'Total market value ($)', angle: 90, position: 'insideRight', style: { textAnchor: 'middle' }, fill: '#3b82f6', fontSize: 10 }}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: 'hsl(var(--popover))',
                                borderColor: 'hsl(var(--border))',
                                borderRadius: 'var(--radius)',
                                fontSize: '12px'
                            }}
                            cursor={{ fill: 'hsl(var(--muted)/0.2)' }}
                            formatter={(value: number, name: string) => [
                                formatNumberShort(value),
                                name.charAt(0).toUpperCase() + name.slice(1)
                            ]}
                        />
                        <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />

                        {/* Calls */}
                        <Bar
                            yAxisId="left"
                            dataKey="calls"
                            name="Calls"
                            fill="#22c55e"
                            opacity={0.8}
                            radius={[2, 2, 0, 0]}
                        />

                        {/* Puts */}
                        <Bar
                            yAxisId="left"
                            dataKey="puts"
                            name="Puts"
                            fill="#ef4444"
                            opacity={0.8}
                            radius={[2, 2, 0, 0]}
                        />

                        {/* Pain Line (Blue) */}
                        <Line
                            yAxisId="right"
                            type="monotone"
                            dataKey="pain"
                            name="Pain"
                            stroke="#3b82f6"
                            strokeWidth={2}
                            strokeDasharray="3 3"
                            dot={false}
                        />

                        {/* Max Pain Highlight */}
                        {maxPain && (
                            <ReferenceLine
                                yAxisId="left"
                                x={maxPain}
                                stroke="#f59e0b"
                                strokeWidth={1}
                                strokeDasharray="3 3"
                                label={{
                                    value: `Max Pain: ${maxPain}`,
                                    position: 'insideTopRight',
                                    fill: '#f59e0b',
                                    fontSize: 10,
                                    // fontWeight: 'bold',
                                    dy: 10
                                }}
                            />
                        )}

                        {/* Reference Line for Current Price - Snapped to closest strike */}
                        {currentPrice && (() => {
                            if (chartData.length === 0) return null;
                            // Find closest strike
                            const closest = chartData.reduce((prev: any, curr: any) => {
                                return (Math.abs(curr.strike - currentPrice) < Math.abs(prev.strike - currentPrice) ? curr : prev);
                            });

                            return (
                                <ReferenceLine
                                    yAxisId="left"
                                    x={closest.strike}
                                    stroke="hsl(var(--foreground))"
                                    strokeDasharray="3 3"
                                    opacity={0.5}
                                    label={{
                                        value: `Price: ${currentPrice.toFixed(2)}`,
                                        position: 'insideTopRight',
                                        fill: 'hsl(var(--foreground))',
                                        fontSize: 10
                                    }}
                                />
                            );
                        })()}

                        {/* Max Pain Reference (already covered by Pain Line minimum, but keeping for specific label if needed) */}
                        {/* We could add it, but the Curve shows it. Let's keep it simple. */}
                    </ComposedChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};
