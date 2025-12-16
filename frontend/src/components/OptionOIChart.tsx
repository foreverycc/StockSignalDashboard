import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    ReferenceLine
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
                    <BarChart
                        data={chartData}
                        margin={{ top: 20, right: 55, left: 20, bottom: 5 }}
                        barGap={0}
                    >
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                        <XAxis
                            dataKey="strike"
                            tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                            tickLine={true}
                            axisLine={true}
                        />
                        <YAxis
                            tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                            tickLine={true}
                            axisLine={true}
                            tickFormatter={(value) => formatNumberShort(value)}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: 'hsl(var(--card))',
                                borderColor: 'hsl(var(--border))',
                                borderRadius: '8px',
                                fontSize: '12px'
                            }}
                            cursor={{ fill: 'hsl(var(--muted)/0.2)' }}
                        />
                        <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />

                        {/* Calls */}
                        <Bar
                            dataKey="calls"
                            name="Calls"
                            fill="#22c55e"
                            opacity={0.8}
                            radius={[2, 2, 0, 0]}
                        />

                        {/* Puts */}
                        <Bar
                            dataKey="puts"
                            name="Puts"
                            fill="#ef4444"
                            opacity={0.8}
                            radius={[2, 2, 0, 0]}
                        />

                        {/* Reference Line for Current Price - Snapped to closest strike */}
                        {currentPrice && (() => {
                            // Find closest strike
                            const closest = chartData.reduce((prev: any, curr: any) => {
                                return (Math.abs(curr.strike - currentPrice) < Math.abs(prev.strike - currentPrice) ? curr : prev);
                            });

                            return (
                                <ReferenceLine
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
                        {/* 
                            Note: ReferenceLine 'x' matches 'dataKey' if it's categorical. 
                            If strike is numerical, XAxis needs 'type="number"'.
                            Normally chartData strikes are numbers. 
                            Let's force XAxis type="number" and domain/ticks properly if needed,
                            or Recharts handles it if 'dataKey' is numeric.
                            Usually for BarChart, XAxis is categorical by default.
                            If categorical, ReferenceLine x must be an exact match to a category value.
                            If currentPrice is 151.2 and strikes are 150, 155, ReferenceLine won't show on categorical axis.
                            
                            Better approach:
                            Find closest strike to currentPrice to attach the label, or just show it roughly?
                            Or switch to Type="number" for XAxis. 
                        */}
                    </BarChart>
                </ResponsiveContainer>
            </div>
            {currentPrice && (
                <div className="text-center text-xs text-muted-foreground mt-2">
                    Current Price: {currentPrice.toFixed(2)}
                </div>
            )}
        </div>
    );
};
