import React from 'react';
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
    ReferenceLine
} from 'recharts';
import { processRowDataForChart, extractCurrentTrajectory } from '../utils/chartUtils';

interface BoxplotChartProps {
    selectedRow: any | null;
    title?: string;
    subtitle?: string;
}

export const BoxplotChart: React.FC<BoxplotChartProps> = ({ selectedRow, title, subtitle }) => {
    console.log('BoxplotChart received selectedRow:', selectedRow);

    if (!selectedRow) {
        return <div className="flex items-center justify-center h-full text-muted-foreground">No data available</div>;
    }

    // Process historical data for boxplot
    const boxplotData = processRowDataForChart(selectedRow);
    console.log('BoxplotChart boxplotData:', boxplotData);

    if (boxplotData.length === 0) {
        console.log('BoxplotChart: No boxplot data - this file type does not have detailed historical data');
        return (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground text-sm p-4 text-center">
                <p className="mb-2">No historical data available for this interval.</p>
                <p className="text-xs">For details, please go to <span className="font-semibold">Detailed Results</span> tab.</p>
            </div>
        );
    }

    // Extract current signal trajectory
    const currentTrajectory = extractCurrentTrajectory(selectedRow);
    const currentPeriod = parseInt(selectedRow.current_period) || 0;

    // Combine data for chart
    const chartData = boxplotData.map(d => ({
        ...d,
        iqrBase: d.q1 || 0,
        iqrRange: (d.q3 || 0) - (d.q1 || 0),
        currentReturn: (d.period <= currentPeriod && currentTrajectory.returns[d.period] !== undefined)
            ? currentTrajectory.returns[d.period]
            : null,
        currentVolume: (d.period <= currentPeriod && currentTrajectory.volumes[d.period] !== undefined)
            ? currentTrajectory.volumes[d.period]
            : null
    }));

    // Create data for volume chart (separate)
    const volumeData = chartData.map(d => ({
        period: d.period,
        volume: d.avgVolume,
        currentVolume: d.currentVolume
    }));

    return (
        <div className="w-full h-full flex flex-col">
            <div className="mb-2">
                {title && <h3 className="text-sm font-semibold">{title}</h3>}
                {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
            </div>

            {/* Returns Chart - Top */}
            <div className="w-full mb-1" style={{ height: '200px' }}>
                <ResponsiveContainer width="100%" height={200}>
                    <ComposedChart
                        data={chartData}
                        margin={{ top: 5, right: 55, left: 20, bottom: 5 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis
                            dataKey="period"
                            stroke="hsl(var(--muted-foreground))"
                            tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                            hide
                        />
                        <YAxis
                            stroke="hsl(var(--muted-foreground))"
                            tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                            label={{ value: 'Return (%)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle' }, fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: 'hsl(var(--card))',
                                borderColor: 'hsl(var(--border))',
                                color: 'hsl(var(--card-foreground))',
                                fontSize: '11px'
                            }}
                            formatter={(value: any, name: string) => [typeof value === 'number' ? value.toFixed(2) + '%' : value, name]}
                        />
                        <Legend wrapperStyle={{ fontSize: '11px' }} align="center" />
                        <ReferenceLine y={0} stroke="hsl(var(--muted-foreground))" strokeDasharray="3 3" />

                        {/* Min/Max - light gray dashed line */}
                        <Line
                            type="monotone"
                            dataKey="max"
                            stroke="hsl(var(--muted-foreground))"
                            strokeWidth={1}
                            strokeOpacity={0.62}
                            strokeDasharray="4 4"
                            dot={false}
                            name="Min/Max" // Merge Min/Max name here
                        />
                        <Line
                            type="monotone"
                            dataKey="min"
                            stroke="hsl(var(--muted-foreground))"
                            strokeWidth={1}
                            strokeOpacity={0.62}
                            strokeDasharray="4 4"
                            dot={false}
                            name="Min"
                            legendType="none" // Hide Min legend
                        />

                        {/* Q1-Q3 Interquartile Range - light blue fill using stacked bar */}
                        <Bar
                            dataKey="iqrBase"
                            fill="transparent"
                            stackId="iqr"
                            legendType="none"
                        />
                        <Bar
                            dataKey="iqrRange"
                            fill="hsl(var(--primary))"
                            fillOpacity={0.2}
                            stackId="iqr"
                            name="IQR (Q1/Q3)"
                            legendType="none" // Hide bar legend
                        />

                        {/* Q1 and Q3 lines - blue dashed */}
                        <Line
                            type="monotone"
                            dataKey="q3"
                            stroke="hsl(var(--primary))"
                            strokeWidth={1}
                            strokeDasharray="3 3"
                            dot={false}
                            name="Q3"
                            legendType="none" // Merged into Q1/Q3
                        />
                        <Line
                            type="monotone"
                            dataKey="q1"
                            stroke="hsl(var(--primary))"
                            strokeWidth={1}
                            strokeDasharray="3 3"
                            dot={false}
                            name="Q1/Q3" // Visible Legend Item
                        />

                        {/* Median - small blue dots only */}
                        <Line
                            type="monotone"
                            dataKey="median"
                            stroke="hsl(var(--primary))"
                            strokeWidth={1}
                            dot={{ r: 1, fill: 'hsl(var(--primary))' }}
                            name="Median"
                        />

                        {/* Current return - red solid line */}
                        <Line
                            type="monotone"
                            dataKey="currentReturn"
                            stroke="#ef4444"
                            strokeWidth={1}
                            dot={{ r: 1, fill: '#ef4444' }}
                            name="Current"
                        />
                    </ComposedChart>
                </ResponsiveContainer>
            </div>

            {/* Volume Chart - Bottom */}
            <div className="w-full" style={{ height: '100px' }}>
                <ResponsiveContainer width="100%" height={100}>
                    <ComposedChart
                        data={volumeData}
                        margin={{ top: 0, right: 55, left: 20, bottom: 20 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis
                            dataKey="period"
                            stroke="hsl(var(--muted-foreground))"
                            tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                            label={{ value: 'Period', position: 'insideBottom', offset: -10, fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                        />
                        <YAxis
                            stroke="hsl(var(--muted-foreground))"
                            tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                            label={{ value: 'Vol', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle' }, fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: 'hsl(var(--card))',
                                borderColor: 'hsl(var(--border))',
                                color: 'hsl(var(--card-foreground))',
                                fontSize: '11px'
                            }}
                            formatter={(value: any) => [Math.round(value).toLocaleString(), 'Avg Volume']}
                        />
                        <Bar
                            dataKey="volume"
                            fill="hsl(var(--muted-foreground))"
                            opacity={0.5}
                            name="Avg Volume"
                        />

                        {/* Current volume - red solid line */}
                        <Line
                            type="monotone"
                            dataKey="currentVolume"
                            stroke="#ef4444"
                            strokeWidth={1}
                            dot={{ r: 1, fill: '#ef4444' }}
                            name="Current Volume"
                        />
                    </ComposedChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};
