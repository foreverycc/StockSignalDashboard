import React, { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { analysisApi, stocksApi } from '../services/api';
import { AnalysisTable } from '../components/AnalysisTable';
import { BoxplotChart } from '../components/BoxplotChart';
import { LogViewer } from '../components/LogViewer';
import { Play, RefreshCw, Clock, AlertCircle, Terminal } from 'lucide-react';
import { cn } from '../utils/cn';

export const Dashboard: React.FC = () => {

    const [selectedStockList, setSelectedStockList] = useState<string>('');
    const [activeTab, setActiveTab] = useState<'cd' | 'mc'>('cd');
    const [activeSubTab, setActiveSubTab] = useState<string>('best_intervals_50');
    const [selectedRow, setSelectedRow] = useState<any>(null);
    const [chartData, setChartData] = useState<any[]>([]);
    const [showLogs, setShowLogs] = useState(false);

    // Fetch stock lists
    const { data: stockLists } = useQuery({
        queryKey: ['stockFiles'],
        queryFn: stocksApi.list
    });

    // Set default stock list
    useEffect(() => {
        if (stockLists && stockLists.length > 0 && !selectedStockList) {
            if (stockLists.includes('00-stocks_hot.tab')) {
                setSelectedStockList('00-stocks_hot.tab');
            } else {
                setSelectedStockList(stockLists[0]);
            }
        }
    }, [stockLists, selectedStockList]);

    // Fetch job status
    const { data: jobStatus, refetch: refetchStatus } = useQuery({
        queryKey: ['jobStatus'],
        queryFn: analysisApi.getStatus,
        refetchInterval: (query) => (query.state.data?.status === 'running' ? 1000 : false)
    });

    // Run analysis mutation
    const runAnalysisMutation = useMutation({
        mutationFn: () => analysisApi.run(selectedStockList),
        onSuccess: () => {
            refetchStatus();
        },
        onError: (error) => alert(`Error starting analysis: ${error}`)
    });

    // Fetch result files
    const { data: resultFiles, isLoading: isLoadingFiles } = useQuery({
        queryKey: ['resultFiles', selectedStockList],
        queryFn: () => analysisApi.listFiles(selectedStockList),
        enabled: !!selectedStockList
    });

    // Fetch latest update time
    const { data: latestUpdate } = useQuery({
        queryKey: ['latestUpdate', selectedStockList],
        queryFn: () => selectedStockList ? analysisApi.getLatestUpdate(selectedStockList) : null,
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

    // Fetch chart data when row is selected
    // We need to find the returns distribution file
    const returnsFileName = React.useMemo(() => {
        if (!resultFiles) return null;
        const prefix = activeTab === 'cd' ? 'cd_eval_returns_distribution_' : 'mc_eval_returns_distribution_';
        return resultFiles.find(f => f.startsWith(prefix));
    }, [resultFiles, activeTab]);

    const { data: returnsData } = useQuery({
        queryKey: ['returnsData', returnsFileName],
        queryFn: () => returnsFileName ? analysisApi.getFileContent(returnsFileName) : null,
        enabled: !!returnsFileName
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
            if (!intervalsStr) return [];

            // Parse intervals: "1,2,3" -> ["1h", "2h", "3h"] or "10,15,30" -> ["10m", "15m", "30m"]
            const intervalNumbers = intervalsStr.split(',').map((s: string) => s.trim());
            const suffix = activeSubTab === '1234' ? 'h' : 'm';
            const intervals = intervalNumbers.map((n: string) => n + suffix);

            // Find detailed rows for each interval
            return intervals.map(interval =>
                detailedData.find((d: any) =>
                    d.ticker === selectedRow.ticker && d.interval === interval
                )
            ).filter(Boolean); // Remove any undefined entries
        }

        // For other tabs, match by ticker and interval
        const match = detailedData.find((d: any) =>
            d.ticker === selectedRow.ticker && d.interval === selectedRow.interval
        );
        return match ? [match] : [];
    }, [selectedRow, detailedData, activeSubTab]);

    // Process chart data
    useEffect(() => {
        if (selectedRow && returnsData) {
            const filtered = returnsData.filter((d: any) =>
                d.ticker === selectedRow.ticker && d.interval === selectedRow.interval
            );
            // Sort by period
            filtered.sort((a: any, b: any) => a.period - b.period);
            setChartData(filtered);
        } else {
            setChartData([]);
        }
    }, [selectedRow, returnsData]);

    const handleRunAnalysis = () => {
        if (selectedStockList) {
            runAnalysisMutation.mutate();
        }
    };

    return (
        <div className="p-6 h-full flex flex-col space-y-6">
            {/* Header & Controls */}
            <div className="flex justify-between items-center bg-card p-4 rounded-xl border border-border shadow-sm">
                <div className="flex items-center gap-4">
                    <div>
                        <label className="block text-xs font-medium text-muted-foreground mb-1">Stock List</label>
                        <select
                            value={selectedStockList}
                            onChange={(e) => setSelectedStockList(e.target.value)}
                            className="px-3 py-2 rounded-md border border-input bg-background text-sm min-w-[200px] focus:outline-none focus:ring-2 focus:ring-primary/50"
                        >
                            {stockLists?.map(f => <option key={f} value={f}>{f}</option>)}
                        </select>
                    </div>

                    {latestUpdate?.timestamp && (
                        <div className="flex flex-col justify-center">
                            <span className="text-xs font-medium text-muted-foreground">Last Updated</span>
                            <span className="text-sm flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {new Date(latestUpdate.timestamp * 1000).toLocaleString()}
                            </span>
                        </div>
                    )}
                </div>

                <div className="flex items-center gap-4">
                    {jobStatus?.status === 'failed' && (
                        <div className="flex items-center gap-2 text-destructive text-sm font-medium bg-destructive/10 px-3 py-2 rounded-lg border border-destructive/20">
                            <AlertCircle className="w-4 h-4" />
                            Analysis Failed: {jobStatus.error || 'Unknown error'}
                        </div>
                    )}
                    {jobStatus?.status === 'running' ? (
                        <div className="flex items-center gap-3 px-4 py-2 bg-primary/10 text-primary rounded-lg border border-primary/20 cursor-pointer hover:bg-primary/20 transition-colors" onClick={() => setShowLogs(true)}>
                            <RefreshCw className="w-4 h-4 animate-spin" />
                            <div className="flex flex-col">
                                <span className="text-sm font-medium">Running Analysis...</span>
                                <span className="text-xs opacity-80">Progress: {jobStatus.progress}% (Click for logs)</span>
                            </div>
                        </div>
                    ) : (
                        <div className="flex gap-2">
                            <button
                                onClick={() => setShowLogs(!showLogs)}
                                className="p-2.5 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-all shadow-sm"
                                title="View Logs"
                            >
                                <Terminal className="w-4 h-4" />
                            </button>
                            <button
                                onClick={handleRunAnalysis}
                                disabled={!selectedStockList}
                                className="flex items-center gap-2 px-6 py-2.5 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-all shadow-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <Play className="w-4 h-4" />
                                Run Analysis
                            </button>
                        </div>
                    )}
                </div>
            </div>

            <LogViewer isOpen={showLogs} onClose={() => setShowLogs(false)} />

            {/* Main Content */}
            <div className="flex-1 flex flex-col bg-card rounded-xl border border-border shadow-sm overflow-hidden">
                {/* Tabs */}
                <div className="flex border-b border-border">
                    <button
                        onClick={() => setActiveTab('cd')}
                        className={cn(
                            "px-6 py-3 text-sm font-medium transition-colors relative",
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
                            "px-6 py-3 text-sm font-medium transition-colors relative",
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
                    <div className="flex gap-1 border-b border-border">
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
                                    "px-4 py-2 text-sm font-medium transition-colors relative",
                                    activeSubTab === tab.value
                                        ? "text-primary border-b-2 border-primary"
                                        : "text-muted-foreground hover:text-foreground"
                                )}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>
                )}

                {activeTab === 'mc' && (
                    <div className="flex gap-1 border-b border-border">
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
                                    "px-4 py-2 text-sm font-medium transition-colors relative",
                                    activeSubTab === tab.value
                                        ? "text-primary border-b-2 border-primary"
                                        : "text-muted-foreground hover:text-foreground"
                                )}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>
                )}

                {/* Content Area */}
                <div className="flex-1 flex overflow-hidden">
                    {/* Table */}
                    <div className={cn("flex-1 border-r border-border", selectedRow ? "w-2/3" : "w-full")}>
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

                    {/* Chart / Details Panel */}
                    {selectedRow && (
                        <div className="w-1/3 flex flex-col bg-card">
                            <div className="p-4 border-b border-border flex justify-between items-center bg-muted/10">
                                <h3 className="font-semibold">{selectedRow.ticker} ({selectedRow.interval})</h3>
                                <button
                                    onClick={() => setSelectedRow(null)}
                                    className="text-muted-foreground hover:text-foreground"
                                >
                                    Close
                                </button>
                            </div>
                            <div className="flex-1 p-4 overflow-y-auto">
                                {/* Returns Distribution Boxplot(s) */}
                                {detailedRows.length > 0 ? (
                                    <div className="space-y-6">
                                        {detailedRows.map((row, index) => (
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

                                <div className="space-y-4">
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
