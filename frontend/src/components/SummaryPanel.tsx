import React, { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { analysisApi } from '../services/api';
import { MarketBreadthChart } from './MarketBreadthChart';
import { cn } from '../utils/cn';
import { subYears, subMonths, subDays, parseISO, isAfter, format } from 'date-fns';
import { DetailedChartRow, InteractiveOptionChart } from '../pages/Dashboard';

const FetchingChartView = ({ row, type, runId, onClose }: { row: any, type: 'bull' | 'bear', runId: number | undefined, onClose: () => void }) => {
    // Fetch detailed data for this ticker
    const resultType = type === 'bull' ? 'cd_eval_custom_detailed' : 'mc_eval_custom_detailed';

    const { data: detailedData, isLoading } = useQuery({
        queryKey: ['detailedRowData', runId, resultType, row.ticker],
        queryFn: () => runId ? analysisApi.getResult(runId, resultType, row.ticker) : null,
        enabled: !!runId && !!row.ticker
    });

    // Find the matching interval row from detailed data
    const detailedRow = useMemo(() => {
        if (!detailedData || !Array.isArray(detailedData)) return null;
        return detailedData.find((d: any) => d.interval === row.interval) || detailedData[0];
    }, [detailedData, row.interval]);

    return (
        <div className="flex flex-col border rounded-lg bg-card overflow-hidden h-[800px] shadow-lg">
            <div className="p-3 border-b bg-muted/30 flex justify-between items-center sticky top-0 z-10 backdrop-blur">
                <div>
                    <span className="font-medium pl-2 text-lg">{row.ticker}</span>
                    <span className="text-muted-foreground text-sm ml-2">({row.interval}) - {type === 'bull' ? 'Bullish' : 'Bearish'}</span>
                </div>
                <button
                    onClick={onClose}
                    className="px-3 py-1.5 text-sm hover:bg-red-500/10 hover:text-red-500 rounded border border-transparent hover:border-red-200 transition-colors"
                >
                    Close
                </button>
            </div>
            <div className="p-4 flex-1 overflow-y-auto space-y-6">
                {isLoading ? (
                    <div className="flex items-center justify-center h-40 text-muted-foreground">
                        Loading detailed analysis...
                    </div>
                ) : detailedRow ? (
                    <>
                        <DetailedChartRow row={detailedRow} activeSubTab="summary" />

                        {/* Option Chart */}
                        <div style={{ height: '350px' }} className="p-4 border rounded-lg bg-card/50 mt-6">
                            <InteractiveOptionChart ticker={row.ticker} />
                        </div>
                    </>
                ) : (
                    <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
                        <p>No detailed data available.</p>
                        <p className="text-xs mt-2">Try checking the "Detailed Results" tab.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

interface SummaryPanelProps {
    runId: number | undefined;
    onRowClick?: (row: any, type: 'bull' | 'bear') => void;
}

export const SummaryPanel: React.FC<SummaryPanelProps> = ({ runId }) => {

    // --- Data Fetching ---

    // State for In-Line Chart
    const [selectedRow, setSelectedRow] = React.useState<any | null>(null);
    const [selectedType, setSelectedType] = React.useState<'bull' | 'bear' | null>(null);

    const handleRowClick = (row: any, type: 'bull' | 'bear') => {
        if (selectedRow?.ticker === row.ticker && selectedType === type) {
            // Toggle off if clicking same row
            setSelectedRow(null);
            setSelectedType(null);
        } else {
            setSelectedRow(row);
            setSelectedType(type);
        }
    };

    // 1. SPX Data
    const { data: spxHistory } = useQuery({
        queryKey: ['priceHistory', '^SPX', '1d'], // Daily resolution for high level chart
        queryFn: () => analysisApi.getPriceHistory('^SPX', '1d'),
        staleTime: 1000 * 60 * 60, // 1 hour
    });

    // 2. Market Breadth Data
    // We fetch all 4 types
    const { data: breadthCD1234 } = useQuery({
        queryKey: ['breadth', runId, 'cd_market_breadth_1234'],
        queryFn: () => runId ? analysisApi.getResult(runId, 'cd_market_breadth_1234') : null,
        enabled: !!runId
    });
    const { data: breadthCD5230 } = useQuery({
        queryKey: ['breadth', runId, 'cd_market_breadth_5230'],
        queryFn: () => runId ? analysisApi.getResult(runId, 'cd_market_breadth_5230') : null,
        enabled: !!runId
    });
    const { data: breadthMC1234 } = useQuery({
        queryKey: ['breadth', runId, 'mc_market_breadth_1234'],
        queryFn: () => runId ? analysisApi.getResult(runId, 'mc_market_breadth_1234') : null,
        enabled: !!runId
    });
    const { data: breadthMC5230 } = useQuery({
        queryKey: ['breadth', runId, 'mc_market_breadth_5230'],
        queryFn: () => runId ? analysisApi.getResult(runId, 'mc_market_breadth_5230') : null,
        enabled: !!runId
    });

    // 3. High Return Opportunities (Best Intervals 50)
    // Fetching just 50 period range for summary
    const { data: bestCD } = useQuery({
        queryKey: ['best', runId, 'cd_eval_best_intervals_50'],
        queryFn: () => runId ? analysisApi.getResult(runId, 'cd_eval_best_intervals_50') : null,
        enabled: !!runId
    });
    const { data: bestMC } = useQuery({
        queryKey: ['best', runId, 'mc_eval_best_intervals_50'],
        queryFn: () => runId ? analysisApi.getResult(runId, 'mc_eval_best_intervals_50') : null,
        enabled: !!runId
    });

    // Date Filters
    const oneYearAgo = useMemo(() => subYears(new Date(), 1), []);
    const oneMonthAgo = useMemo(() => subMonths(new Date(), 1), []);

    // --- Helpers ---
    const formatPercent = (val: number) => `${val.toFixed(1)}%`;

    const ChartView = ({ row }: { row: any }) => (
        <div className="flex flex-col border rounded-lg bg-card overflow-hidden h-[400px]">
            <div className="p-2 border-b bg-muted/30 flex justify-between items-center">
                <span className="font-medium pl-2">Analysis: {row.ticker}</span>
                <button
                    onClick={() => { setSelectedRow(null); setSelectedType(null); }}
                    className="px-2 py-1 text-xs hover:bg-muted rounded border border-transparent hover:border-border"
                >
                    Close
                </button>
            </div>
            <div className="p-2 flex-1 min-h-0 overflow-y-auto">
                <DetailedChartRow row={row} activeSubTab="summary" />
            </div>
        </div>
    );

    const TopTable = ({ data, title, type, onRowClick }: {
        data: any[],
        title: string,
        type: 'bull' | 'bear',
        onRowClick?: (row: any, type: 'bull' | 'bear') => void
    }) => {
        if (!data || data.length === 0) return null;

        // Take top 10 sorted by return magnitude, filtered by last 7 days
        const sorted = useMemo(() => {
            const cutoffDate = subDays(new Date(), 7);

            return [...data]
                .filter(row => {
                    if (!row.latest_signal) return false;
                    // Assuming latest_signal is ISO-like string. parseISO handles it.
                    // If it's just YYYY-MM-DD, it works too.
                    try {
                        const date = parseISO(row.latest_signal);
                        return isAfter(date, cutoffDate);
                    } catch (e) {
                        return false;
                    }
                })
                .sort((a, b) =>
                    type === 'bull' ? b.avg_return - a.avg_return : a.avg_return - b.avg_return
                )
                .slice(0, 10);
        }, [data, type]);

        if (sorted.length === 0) return null;

        return (
            <div className="flex flex-col border rounded-lg bg-card overflow-hidden">
                <div className="p-3 bg-muted/30 border-b font-medium flex justify-between">
                    <span>{title}</span>
                    <span className="text-xs text-muted-foreground font-normal mt-1">(Last 7 Days)</span>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="bg-muted/10 text-muted-foreground">
                            <tr>
                                <th className="p-2 text-left">Ticker</th>
                                <th className="p-2 text-left">Date</th>
                                <th className="p-2 text-left">Intv</th>
                                <th className="p-2 text-right">Return</th>
                                <th className="p-2 text-right">Win Rate</th>
                                <th className="p-2 text-right">Count</th>
                            </tr>
                        </thead>
                        <tbody>
                            {sorted.map((row, i) => (
                                <tr
                                    key={i}
                                    className="border-b last:border-0 hover:bg-muted/10 cursor-pointer transition-colors"
                                    onClick={() => onRowClick?.(row, type)}
                                >
                                    <td className="p-2 font-medium">{row.ticker}</td>
                                    <td className="p-2 text-muted-foreground text-xs">
                                        {row.latest_signal ? format(parseISO(row.latest_signal), 'MM-dd HH:mm') : '-'}
                                    </td>
                                    <td className="p-2 text-muted-foreground">{row.interval}</td>
                                    <td className={cn("p-2 text-right font-medium", type === 'bull' ? "text-green-500" : "text-red-500")}>
                                        {formatPercent(row.avg_return)}
                                    </td>
                                    <td className="p-2 text-right">{formatPercent(row.success_rate)}</td>
                                    <td className="p-2 text-right">{row.test_count}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        );
    };

    return (
        <div className="p-4 md:p-6 h-full overflow-y-auto space-y-6">

            {/* Market Breadth Charts */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <MarketBreadthChart
                    title="Market Breadth: CD 1234 Buy Signals vs SPX"
                    spxData={spxHistory ?? []}
                    breadthData={breadthCD1234 ?? []}
                    breadthLabel="New Buy Signals"
                    color="#22c55e" // Green
                    minDate={oneYearAgo}
                />
                <MarketBreadthChart
                    title="Market Breadth: MC 1234 Sell Signals vs SPX"
                    spxData={spxHistory ?? []}
                    breadthData={breadthMC1234 ?? []}
                    breadthLabel="New Sell Signals"
                    color="#ef4444" // Red
                    minDate={oneYearAgo}
                />
            </div>

            {/* Secondary Breadth (Collapsible or just below? Let's fit them below if data exists) */}
            {((breadthCD5230?.length ?? 0) > 0 || (breadthMC5230?.length ?? 0) > 0) && (
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 opacity-80">
                    <MarketBreadthChart
                        title="Market Breadth: CD 5230 Buy Signals vs SPX"
                        spxData={spxHistory ?? []}
                        breadthData={breadthCD5230 ?? []}
                        breadthLabel="New Buy Signals"
                        color="#10b981" // Emerald
                        minDate={oneMonthAgo}
                    />
                    <MarketBreadthChart
                        title="Market Breadth: MC 5230 Sell Signals vs SPX"
                        spxData={spxHistory ?? []}
                        breadthData={breadthMC5230 ?? []}
                        breadthLabel="New Sell Signals"
                        color="#f43f5e" // Rose
                        minDate={oneMonthAgo}
                    />
                </div>
            )}

            <div className="border-t border-border pt-6"></div>

            {/* High Return Opportunities */}
            <div>
                <h2 className="text-xl font-bold mb-4">High Return Opportunities (Top 10)</h2>
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                    {/* Left Column: CD Table OR Chart for MC Selection */}
                    {selectedType === 'bear' && selectedRow ? (
                        <FetchingChartView
                            row={selectedRow}
                            type="bear"
                            runId={runId}
                            onClose={() => { setSelectedRow(null); setSelectedType(null); }}
                        />
                    ) : (
                        <TopTable
                            data={bestCD ?? []}
                            title="CD Bullish (Best Intervals)"
                            type="bull"
                            onRowClick={handleRowClick}
                        />
                    )}

                    {/* Right Column: MC Table OR Chart for CD Selection */}
                    {selectedType === 'bull' && selectedRow ? (
                        <FetchingChartView
                            row={selectedRow}
                            type="bull"
                            runId={runId}
                            onClose={() => { setSelectedRow(null); setSelectedType(null); }}
                        />
                    ) : (
                        <TopTable
                            data={bestMC ?? []}
                            title="MC Bearish (Best Intervals)"
                            type="bear"
                            onRowClick={handleRowClick}
                        />
                    )}
                </div>
            </div>
        </div>
    );
};
