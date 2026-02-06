import React, { useMemo, useRef, useState, useCallback, useEffect } from 'react';
import {
    ComposedChart,
    Line,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    ReferenceArea
} from 'recharts';
import { format } from 'date-fns';

interface BreadthDataPoint {
    date: string;
    count: number;
}

interface PriceDataPoint {
    time: string;
    close: number;
}

interface MarketBreadthChartProps {
    title: string;
    spxData: PriceDataPoint[];
    breadthData: BreadthDataPoint[];
    breadthLabel: string;
    color?: string;
    minDate?: Date;
}

export const MarketBreadthChart: React.FC<MarketBreadthChartProps> = ({
    title,
    spxData,
    breadthData,
    breadthLabel,
    color = "#8884d8",
    minDate
}) => {
    // --- Zoom State & Logic (Adapted from CandleChart) ---
    const [zoomState, setZoomState] = useState<{ start: number, end: number } | null>(null);
    const [selection, setSelection] = useState<{ start: number, end: number } | null>(null);
    const isSelectingRef = useRef(false);
    const chartContainerRef = useRef<HTMLDivElement>(null);

    // Merge data by date
    const mergedData = useMemo(() => {
        const dataMap = new Map<string, any>();

        // Process SPX Data
        spxData.forEach(p => {
            const dateStr = p.time.split('T')[0]; // Extract YYYY-MM-DD
            if (!dataMap.has(dateStr)) {
                dataMap.set(dateStr, { date: dateStr });
            }
            dataMap.get(dateStr).spx = p.close;
        });

        // Process Breadth Data
        breadthData.forEach(b => {
            const dateStr = b.date;
            if (!dataMap.has(dateStr)) {
                dataMap.set(dateStr, { date: dateStr });
            }
            dataMap.get(dateStr).count = b.count;
        });

        // Convert to array and sort
        let result = Array.from(dataMap.values())
            .sort((a, b) => a.date.localeCompare(b.date));

        if (minDate) {
            const minStr = format(minDate, 'yyyy-MM-dd');
            result = result.filter(d => d.date >= minStr);
        }

        // Filter out days without SPX data (Market Closed/Weekends)
        result = result.filter(d => d.spx !== undefined);

        return result;
    }, [spxData, breadthData, minDate]);

    // Visible slice
    const visibleData = useMemo(() => {
        if (mergedData.length === 0) return [];
        if (!zoomState) return mergedData;
        return mergedData.slice(zoomState.start, zoomState.end + 1);
    }, [mergedData, zoomState]);


    // Helpers
    const getChartArea = (container: HTMLElement) => {
        // Approximate for mouse tracking. The ComposedChart has internal margins.
        // We'll use width based logic.
        const width = container.clientWidth;
        // Recharts default margins or custom? We didn't set margins explicitly in Render but ComposedChart has defaults.
        // Let's assume full width mapping for simplicity or consistent small margins
        const chartWidth = width - 20; // approximate
        if (chartWidth <= 0) return null;
        return { width: chartWidth, left: 10 };
    };

    const pixelToIndex = (x: number, chartArea: { width: number, left: number }, currentCount: number) => {
        const relativeX = x - chartArea.left;
        const fraction = relativeX / chartArea.width;
        const index = Math.floor(fraction * currentCount);
        return Math.max(0, Math.min(currentCount - 1, index));
    };

    // Handlers
    const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
        isSelectingRef.current = true;
        const chartArea = getChartArea(e.currentTarget);
        if (!chartArea) return;
        const count = visibleData.length;
        const clickIndex = pixelToIndex(e.nativeEvent.offsetX, chartArea, count);
        setSelection({ start: clickIndex, end: clickIndex });
    };

    const handleMouseMove = useCallback((e: MouseEvent) => {
        if (!isSelectingRef.current || !chartContainerRef.current) return;
        const chartArea = getChartArea(chartContainerRef.current);
        if (!chartArea) return;
        const count = visibleData.length;
        const moveIndex = pixelToIndex(e.offsetX, chartArea, count);
        setSelection(prev => prev ? { ...prev, end: moveIndex } : null);
    }, [visibleData.length]);

    const handleMouseUp = useCallback(() => {
        if (!isSelectingRef.current) return;
        isSelectingRef.current = false;
        setSelection(prev => {
            if (prev && Math.abs(prev.end - prev.start) > 1) {
                const currentStart = zoomState ? zoomState.start : 0;
                const localMin = Math.min(prev.start, prev.end);
                const localMax = Math.max(prev.start, prev.end);
                const newStart = currentStart + localMin;
                const newEnd = currentStart + localMax;
                setZoomState({ start: newStart, end: newEnd });
            }
            return null;
        });
    }, [zoomState]);

    const handleWheel = (e: React.WheelEvent) => {
        if (visibleData.length === 0) return;
        const currentStart = zoomState ? zoomState.start : 0;
        const currentEnd = zoomState ? zoomState.end : mergedData.length - 1;
        const currentLength = currentEnd - currentStart + 1;
        const zoomFactor = 0.1;
        const delta = e.deltaY > 0 ? 1 : -1;
        const change = Math.max(2, Math.floor(currentLength * zoomFactor));

        let newStart = currentStart;
        let newEnd = currentEnd;

        if (delta > 0) { // Zoom Out
            newStart = Math.max(0, currentStart - Math.ceil(change / 2));
            newEnd = Math.min(mergedData.length - 1, currentEnd + Math.ceil(change / 2));
        } else { // Zoom In
            newStart = Math.min(newEnd - 5, currentStart + Math.ceil(change / 2));
            newEnd = Math.max(newStart + 5, currentEnd - Math.ceil(change / 2));
        }
        setZoomState({ start: newStart, end: newEnd });
    };

    // Global listeners
    useEffect(() => {
        if (chartContainerRef.current) {
            window.addEventListener('mousemove', handleMouseMove);
            window.addEventListener('mouseup', handleMouseUp);
        }
        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
        };
    }, [handleMouseMove, handleMouseUp]);


    if (mergedData.length === 0) {
        return (
            <div className="h-64 flex items-center justify-center border rounded-lg bg-card/50 text-muted-foreground">
                No data available for {title}
            </div>
        );
    }

    return (
        <div className="flex flex-col h-[400px] border rounded-lg bg-card p-4">
            <div className="flex justify-between items-center mb-2">
                <h3 className="text-lg font-semibold text-foreground">{title}</h3>
                <button
                    onClick={() => setZoomState(null)}
                    className="px-2 py-1 text-xs font-medium rounded-md border border-border text-muted-foreground hover:bg-muted"
                >
                    Reset Zoom
                </button>
            </div>
            <div
                ref={chartContainerRef}
                className="flex-1 min-h-0 select-none"
                onMouseDown={handleMouseDown}
                onWheel={handleWheel}
            >
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={visibleData} margin={{ left: 10, right: 10 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                        <XAxis
                            dataKey="date"
                            tickFormatter={(str) => str.substring(5)}
                            minTickGap={30}
                            axisLine={false}
                            tickLine={false}
                        />
                        <YAxis
                            yAxisId="left"
                            orientation="left"
                            stroke={color}
                            axisLine={false}
                            tickLine={false}
                            label={{ value: 'Signal Count', angle: -90, position: 'insideLeft', fill: color }}
                        />
                        <YAxis
                            yAxisId="right"
                            orientation="right"
                            stroke="#82ca9d"
                            domain={['auto', 'auto']}
                            axisLine={false}
                            tickLine={false}
                            label={{ value: 'SPX', angle: 90, position: 'insideRight', fill: '#82ca9d' }}
                            width={50}
                        />
                        <Tooltip
                            contentStyle={{ backgroundColor: 'hsl(var(--background))', borderColor: 'hsl(var(--border))' }}
                            labelStyle={{ color: 'hsl(var(--foreground))' }}
                            labelFormatter={(label) => label}
                        />
                        <Legend wrapperStyle={{ paddingTop: '10px' }} />

                        <Bar
                            yAxisId="left"
                            dataKey="count"
                            name={breadthLabel}
                            fill={color}
                            barSize={20}
                            radius={[4, 4, 0, 0]}
                            opacity={0.8}
                        />
                        <Line
                            yAxisId="right"
                            type="monotone"
                            dataKey="spx"
                            name="SPX Index"
                            stroke="#82ca9d"
                            dot={false}
                            strokeWidth={2}
                        />

                        {selection && visibleData[Math.min(selection.start, selection.end)] && visibleData[Math.max(selection.start, selection.end)] && (
                            <ReferenceArea
                                yAxisId="left"
                                x1={visibleData[Math.min(selection.start, selection.end)].date}
                                x2={visibleData[Math.max(selection.start, selection.end)].date}
                                strokeOpacity={0}
                                fill="hsl(var(--primary))"
                                fillOpacity={0.1}
                            />
                        )}
                    </ComposedChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};
