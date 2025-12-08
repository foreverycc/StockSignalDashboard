import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { analysisApi } from '../services/api';
import { AnalysisTable } from '../components/AnalysisTable';
import { BoxplotChart } from '../components/BoxplotChart';
import { CandleChart } from '../components/CandleChart';
import { LogViewer } from '../components/LogViewer';
import { cn } from '../utils/cn';

interface DashboardProps {
    selectedStockList: string;
    showLogs: boolean;
    setShowLogs: (show: boolean) => void;
}

// Wrapper component to handle individual chart data fetching
const DetailedChartRow = ({ row, activeSubTab }: { row: any, activeSubTab: string }) => {
    const { data: priceHistory, isLoading } = useQuery({
        queryKey: ['priceHistory', row.ticker, row.interval],
        queryFn: () => analysisApi.getPriceHistory(row.ticker, row.interval),
        staleTime: 1000 * 60 * 60 * 24, // 24 hours
        enabled: !!row.ticker && !!row.interval
    });

    return (
        <div className="flex flex-col space-y-4 p-4 border rounded-lg bg-card/50">
            <div style={{ height: '350px' }}>
                <BoxplotChart
                    selectedRow={row}
                    title={`Returns Distribution - ${row.ticker} (${row.interval})`}
                    subtitle={`Success Rate: ${row.success_rate}% | Avg Return: ${row.avg_return}% | Signal Count: ${row.test_count || row.test_count_0 || 'N/A'}`}
                />
            </div>
            <div style={{ height: '500px' }} className="mt-4 border-t pt-4 border-border/50">
                {isLoading ? (
                    <div className="h-full flex items-center justify-center text-muted-foreground">Loading price history...</div>
                ) : (
                    <CandleChart
                        data={priceHistory || []}
                        ticker={row.ticker}
                        interval={row.interval}
                    />
                )}
            </div>
        </div>
    );
};

export const Dashboard: React.FC<DashboardProps> = ({
    selectedStockList,
    showLogs,
    setShowLogs
}) => {
    const [activeTab, setActiveTab] = useState<'cd' | 'mc'>('cd');
    const [activeSubTab, setActiveSubTab] = useState<string>('best_intervals_50');
    const [selectedRow, setSelectedRow] = useState<any>(null);

    // Fetch result files
    const { data: resultFiles, isLoading: isLoadingFiles } = useQuery({
        queryKey: ['resultFiles', selectedStockList],
        queryFn: () => analysisApi.listFiles(selectedStockList),
        enabled: !!selectedStockList
    });

    // Determine which file to load based on active tabs
    const currentFileName = React.useMemo(() => {
        if (!resultFiles) return null;

        let pattern: string;

        // Handle 1234 and 5230 resonance models
        if (activeSubTab === '1234' || activeSubTab === '5230') {
            const prefix = activeTab === 'cd' ? 'cd_breakout_candidates_summary_' : 'mc_breakout_candidates_summary_';
            pattern = prefix + activeSubTab;
        } else {
            // Handle Best Intervals and Custom Detailed
            const prefix = activeTab === 'cd' ? 'cd_eval_' : 'mc_eval_';
            pattern = prefix + activeSubTab;
        }

        return resultFiles.find(f => f.startsWith(pattern));
    }, [resultFiles, activeTab, activeSubTab]);

    // Fetch table data
    const { data: tableData, isLoading: isLoadingTable } = useQuery({
        queryKey: ['tableData', currentFileName],
        queryFn: () => currentFileName ? analysisApi.getFileContent(currentFileName) : null,
        enabled: !!currentFileName
    });

    // Fetch custom_detailed file for chart data (always load this for charts)
    const detailedFileName = React.useMemo(() => {
        if (!resultFiles) return null;
        const prefix = activeTab === 'cd' ? 'cd_eval_custom_detailed_' : 'mc_eval_custom_detailed_';
        return resultFiles.find(f => f.startsWith(prefix));
    }, [resultFiles, activeTab]);

    const { data: detailedData } = useQuery({
        queryKey: ['detailedData', detailedFileName],
        queryFn: () => detailedFileName ? analysisApi.getFileContent(detailedFileName) : null,
        enabled: !!detailedFileName
    });

    // Find matching detailed row(s) for the selected row
    const detailedRows = React.useMemo(() => {
        if (!selectedRow || !detailedData) return [];

        // Helper to extract best metrics from detailed row
        const extractBestMetrics = (row: any) => {
            let bestPeriod = -1;
            let maxSuccessRate = -1;
            let bestReturn = -1;
            let bestCount = 0;

            // Iterate through periods 0-100 to find best stats
            for (let i = 0; i <= 100; i++) {
                const rate = row[`success_rate_${i}`];
                const ret = row[`avg_return_${i}`];
                const count = row[`test_count_${i}`];

                if (rate !== undefined && ret !== undefined) {
                    // Simple logic: maximize success rate, then return
                    if (rate > maxSuccessRate || (rate === maxSuccessRate && ret > bestReturn)) {
                        maxSuccessRate = rate;
                        bestReturn = ret;
                        bestCount = count;
                        bestPeriod = i;
                    }
                }
            }

            return {
                success_rate: maxSuccessRate !== -1 ? maxSuccessRate : 0,
                avg_return: bestReturn !== -1 ? bestReturn : 0,
                test_count: bestCount
            };
        };

        // For 1234/5230 models, the intervals column contains multiple intervals (e.g., "1,2,3")
        if (activeSubTab === '1234' || activeSubTab === '5230') {
            const intervalsStr = selectedRow.intervals;
            if (!intervalsStr) return [];

            // Parse intervals: "1,2,3" -> ["1h", "2h", "3h"] or "10,15,30" -> ["10m", "15m", "30m"]
            const intervalNumbers = intervalsStr.split(',').map((s: string) => s.trim());
            const suffix = activeSubTab === '1234' ? 'h' : 'm';
            const intervals = intervalNumbers.map((n: string) => n + suffix);

            // Find detailed rows for each interval
            const results = intervals.map((interval: any) => {
                const match = detailedData.find((d: any) =>
                    d.ticker === selectedRow.ticker && d.interval === interval
                );

                if (match) {
                    // Calculate best metrics for this interval
                    const metrics = extractBestMetrics(match);
                    return { ...match, ...metrics };
                }
                return match;
            }).filter(Boolean); // Remove any undefined entries

            return results;
        }

        // For other tabs, match by ticker and interval
        const match = detailedData.find((d: any) =>
            d.ticker === selectedRow.ticker && d.interval === selectedRow.interval
        );

        if (match) {
            // Merge metrics from selectedRow (summary) which has the correct values
            return [{
                ...match,
                success_rate: selectedRow.success_rate,
                avg_return: selectedRow.avg_return,
                test_count: selectedRow.test_count || selectedRow.test_count_0
            }];
        }
        return [];
    }, [selectedRow, detailedData, activeSubTab]);

    const [chartPanelWidth, setChartPanelWidth] = useState(33); // Default 33%
    const [isResizing, setIsResizing] = useState(false);

    // Handle resizing
    const startResizing = React.useCallback(() => {
        setIsResizing(true);
    }, []);

    const stopResizing = React.useCallback(() => {
        setIsResizing(false);
    }, []);

    const resize = React.useCallback((mouseMoveEvent: MouseEvent) => {
        if (isResizing) {
            const container = document.getElementById('dashboard-content-container');
            if (container) {
                const containerRect = container.getBoundingClientRect();
                const newWidthPx = containerRect.right - mouseMoveEvent.clientX;
                const newWidthPercent = (newWidthPx / containerRect.width) * 100;

                if (newWidthPercent >= 20 && newWidthPercent <= 80) {
                    setChartPanelWidth(newWidthPercent);
                }
            }
        }
    }, [isResizing]);

    useEffect(() => {
        window.addEventListener("mousemove", resize);
        window.addEventListener("mouseup", stopResizing);
        return () => {
            window.removeEventListener("mousemove", resize);
            window.removeEventListener("mouseup", stopResizing);
        };
    }, [resize, stopResizing]);

    return (
        <div className="p-4 md:p-6 h-full flex flex-col space-y-4 md:space-y-6">
            <LogViewer isOpen={showLogs} onClose={() => setShowLogs(false)} />

            {/* Main Content */}
            <div className="flex-1 flex flex-col bg-card rounded-xl border border-border shadow-sm overflow-hidden">
                {/* Tabs */}
                <div className="flex border-b border-border overflow-x-auto scrollbar-hide">
                    <button
                        onClick={() => setActiveTab('cd')}
                        className={cn(
                            "px-4 md:px-6 py-3 text-sm font-medium transition-colors relative whitespace-nowrap",
                            activeTab === 'cd'
                                ? "text-primary"
                                : "text-muted-foreground hover:text-foreground"
                        )}
                    >
                        CD Analysis (Buy)
                        {activeTab === 'cd' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />}
                    </button>
                    <button
                        onClick={() => setActiveTab('mc')}
                        className={cn(
                            "px-4 md:px-6 py-3 text-sm font-medium transition-colors relative whitespace-nowrap",
                            activeTab === 'mc'
                                ? "text-primary"
                                : "text-muted-foreground hover:text-foreground"
                        )}
                    >
                        MC Analysis (Sell)
                        {activeTab === 'mc' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />}
                    </button>
                </div>

                {/* Subtabs */}
                {activeTab === 'cd' && (
                    <div className="flex gap-1 border-b border-border overflow-x-auto scrollbar-hide p-1">
                        {[
                            { value: 'best_intervals_50', label: 'Best Intervals (50)' },
                            { value: 'best_intervals_20', label: 'Best Intervals (20)' },
                            { value: 'best_intervals_100', label: 'Best Intervals (100)' },
                            { value: 'good_signals', label: 'High Return Intervals' },
                            { value: 'custom_detailed', label: 'Detailed Results' },
                            { value: '1234', label: '1234 Model' },
                            { value: '5230', label: '5230 Model' },
                        ].map((tab) => (
                            <button
                                key={tab.value}
                                onClick={() => setActiveSubTab(tab.value)}
                                className={cn(
                                    "px-3 md:px-4 py-2 text-xs md:text-sm font-medium transition-colors relative whitespace-nowrap rounded-md",
                                    activeSubTab === tab.value
                                        ? "text-primary bg-primary/10"
                                        : "text-muted-foreground hover:text-foreground hover:bg-muted"
                                )}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>
                )}

                {activeTab === 'mc' && (
                    <div className="flex gap-1 border-b border-border overflow-x-auto scrollbar-hide p-1">
                        {[
                            { value: 'best_intervals_50', label: 'Best Intervals (50)' },
                            { value: 'best_intervals_20', label: 'Best Intervals (20)' },
                            { value: 'best_intervals_100', label: 'Best Intervals (100)' },
                            { value: 'good_signals', label: 'High Return Intervals' },
                            { value: 'custom_detailed', label: 'Detailed Results' },
                            { value: '1234', label: '1234 Model' },
                            { value: '5230', label: '5230 Model' },
                        ].map((tab) => (
                            <button
                                key={tab.value}
                                onClick={() => setActiveSubTab(tab.value)}
                                className={cn(
                                    "px-3 md:px-4 py-2 text-xs md:text-sm font-medium transition-colors relative whitespace-nowrap rounded-md",
                                    activeSubTab === tab.value
                                        ? "text-primary bg-primary/10"
                                        : "text-muted-foreground hover:text-foreground hover:bg-muted"
                                )}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>
                )}

                {/* Content Area */}
                <div id="dashboard-content-container" className="flex-1 flex overflow-hidden relative">
                    {/* Table */}
                    <div
                        className={cn("flex-1 border-r border-border overflow-hidden flex flex-col transition-all duration-300")}
                        style={{
                            width: selectedRow && window.innerWidth >= 768 ? `${100 - chartPanelWidth}%` : '100%'
                        }}
                    >
                        {isLoadingTable || isLoadingFiles ? (
                            <div className="h-full flex items-center justify-center text-muted-foreground">Loading data...</div>
                        ) : tableData ? (
                            <AnalysisTable
                                data={tableData}
                                onRowClick={setSelectedRow}
                            />
                        ) : (
                            <div className="h-full flex flex-col items-center justify-center text-muted-foreground p-4 text-center">
                                <p className="mb-2">No data available for {activeSubTab.replace(/_/g, ' ')}</p>
                                <p className="text-xs opacity-70">
                                    Stock List: {selectedStockList || 'None'} <br />
                                    Files Found: {resultFiles?.length || 0} <br />
                                    Target File: {currentFileName || 'Not Found'}
                                </p>
                                {resultFiles && resultFiles.length > 0 && (
                                    <div className="mt-4 text-xs text-left max-h-32 overflow-y-auto border p-2 rounded">
                                        <p className="font-semibold mb-1">Available Files:</p>
                                        {resultFiles.map(f => <div key={f}>{f}</div>)}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Resizer Handle (Desktop Only) */}
                    {selectedRow && (
                        <div
                            className="hidden md:flex w-1 bg-border hover:bg-primary/50 cursor-col-resize transition-colors z-10 items-center justify-center"
                            onMouseDown={startResizing}
                        >
                            <div className="h-8 w-0.5 bg-muted-foreground/30 rounded-full" />
                        </div>
                    )}

                    {/* Chart / Details Panel */}
                    {selectedRow && (
                        <div
                            className={cn(
                                "flex flex-col bg-card overflow-hidden transition-all duration-300 h-full",
                                // Mobile: Fixed overlay
                                "fixed inset-0 z-50 md:static md:z-auto"
                            )}
                            style={{
                                width: window.innerWidth >= 768 ? `${chartPanelWidth}%` : '100%'
                            }}
                        >
                            <div className="p-4 border-b border-border flex justify-between items-center bg-muted/10">
                                <h3 className="font-semibold truncate pr-2">{selectedRow.ticker} ({selectedRow.interval})</h3>
                                <button
                                    onClick={() => setSelectedRow(null)}
                                    className="p-2 -mr-2 text-muted-foreground hover:text-foreground shrink-0"
                                >
                                    Close
                                </button>
                            </div>
                            <div className="flex-1 p-4 overflow-y-auto bg-background md:bg-transparent">
                                {/* Returns Distribution Boxplot(s) & Price History */}
                                {detailedRows.length > 0 ? (
                                    <div className="space-y-6">
                                        {detailedRows.map((row: any, index: number) => (
                                            <DetailedChartRow
                                                key={`${row.ticker}-${row.interval}-${index}`}
                                                row={row}
                                                activeSubTab={activeSubTab}
                                            />
                                        ))}
                                    </div>
                                ) : (
                                    <div className="flex items-center justify-center h-full text-muted-foreground">
                                        No detailed data available for this selection
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
