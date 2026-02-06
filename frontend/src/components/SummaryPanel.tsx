import React, { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { analysisApi } from '../services/api';
import { MarketBreadthChart } from './MarketBreadthChart';
import { cn } from '../utils/cn';
import { subYears, subMonths } from 'date-fns';

interface SummaryPanelProps {
    // ...
    runId: number | undefined;
}

export const SummaryPanel: React.FC<SummaryPanelProps> = ({ runId }) => {

    // --- Data Fetching ---

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

    const TopTable = ({ data, title, type }: { data: any[], title: string, type: 'bull' | 'bear' }) => {
        if (!data || data.length === 0) return null;

        // Take top 10 sorted by return magnitude
        const sorted = useMemo(() => {
            return [...data].sort((a, b) =>
                type === 'bull' ? b.avg_return - a.avg_return : a.avg_return - b.avg_return
            ).slice(0, 10);
        }, [data]);

        return (
            <div className="flex flex-col border rounded-lg bg-card overflow-hidden">
                <div className="p-3 bg-muted/30 border-b font-medium">{title}</div>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="bg-muted/10 text-muted-foreground">
                            <tr>
                                <th className="p-2 text-left">Ticker</th>
                                <th className="p-2 text-left">Intv</th>
                                <th className="p-2 text-right">Return</th>
                                <th className="p-2 text-right">Win Rate</th>
                                <th className="p-2 text-right">Count</th>
                            </tr>
                        </thead>
                        <tbody>
                            {sorted.map((row, i) => (
                                <tr key={i} className="border-b last:border-0 hover:bg-muted/10">
                                    <td className="p-2 font-medium">{row.ticker}</td>
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
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <TopTable data={bestCD ?? []} title="CD Bullish (Best Intervals)" type="bull" />
                    <TopTable data={bestMC ?? []} title="MC Bearish (Best Intervals)" type="bear" />
                    {/* Could add more tables for Good Signals etc if needed */}
                </div>
            </div>
        </div>
    );
};
