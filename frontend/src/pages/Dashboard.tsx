
import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { analysisApi } from '../services/api';
import { AnalysisTable } from '../components/AnalysisTable';
import { BoxplotChart } from '../components/BoxplotChart';
import { LogViewer } from '../components/LogViewer';
import { cn } from '../utils/cn';

interface DashboardProps {
    selectedStockList: string;
    showLogs: boolean;
    setShowLogs: (show: boolean) => void;
}

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

        // For 1234/5230 models, the intervals column contains multiple intervals (e.g., "1,2,3")
        if (activeSubTab === '1234' || activeSubTab === '5230') {
            const intervalsStr = selectedRow.intervals;
            console.log('Processing intervals for row:', selectedRow.ticker, intervalsStr);
            if (!intervalsStr) return [];

            // Parse intervals: "1,2,3" -> ["1h", "2h", "3h"] or "10,15,30" -> ["10m", "15m", "30m"]
            const intervalNumbers = intervalsStr.split(',').map((s: string) => s.trim());
            const suffix = activeSubTab === '1234' ? 'h' : 'm';
            const intervals = intervalNumbers.map((n: string) => n + suffix);
            console.log('Looking for intervals:', intervals);

            // Find detailed rows for each interval
            const results = intervals.map((interval: any) => {
                const match = detailedData.find((d: any) =>
                    d.ticker === selectedRow.ticker && d.interval === interval
                );
                console.log(`Match for ${selectedRow.ticker} ${interval}:`, match ? 'Found' : 'NOT FOUND');
                return match;
            }).filter(Boolean); // Remove any undefined entries

            console.log('Final results count:', results.length);
            return results;
        }

        // For other tabs, match by ticker and interval
        const match = detailedData.find((d: any) =>
            d.ticker === selectedRow.ticker && d.interval === selectedRow.interval
        );
        return match ? [match] : [];
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
                                "flex flex-col bg-card overflow-hidden transition-all duration-300",
                                // Mobile: Fixed overlay
                                "fixed inset-0 z-50 md:static md:z-auto",
                                // Desktop: Dynamic width
                                "md:block"
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
                                {/* Returns Distribution Boxplot(s) */}
                                {detailedRows.length > 0 ? (
                                    <div className="space-y-6">
                                        {detailedRows.map((row: any, index: number) => (
                                            <div key={index} style={{ height: '350px' }}>
                                                <BoxplotChart
                                                    selectedRow={row}
                                                    title={`Returns Distribution - ${row.ticker} (${row.interval})`}
                                                />
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="flex items-center justify-center h-full text-muted-foreground">
                                        No detailed data available for this selection
                                    </div>
                                )}

                                <div className="space-y-4 mt-6">
                                    <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Details</h4>
                                    <div className="grid grid-cols-2 gap-4 text-sm">
                                        <div className="p-3 bg-muted/30 rounded-lg">
                                            <span className="block text-xs text-muted-foreground">Success Rate</span>
                                            <span className="font-mono font-medium">{selectedRow.success_rate}%</span>
                                        </div>
                                        <div className="p-3 bg-muted/30 rounded-lg">
                                            <span className="block text-xs text-muted-foreground">Avg Return</span>
                                            <span className="font-mono font-medium">{selectedRow.avg_return}%</span>
                                        </div>
                                        <div className="p-3 bg-muted/30 rounded-lg">
                                            <span className="block text-xs text-muted-foreground">Signal Count</span>
                                            <span className="font-mono font-medium">{selectedRow.test_count || selectedRow.test_count_0 || 'N/A'}</span>
                                        </div>
                                        <div className="p-3 bg-muted/30 rounded-lg">
                                            <span className="block text-xs text-muted-foreground">Latest Signal</span>
                                            <span className="font-mono font-medium">{selectedRow.latest_signal}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div >
        </div >
    );
};
