import { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider, useQuery, useMutation } from '@tanstack/react-query';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { Configuration } from './pages/Configuration';
import { analysisApi, stocksApi } from './services/api';
import { subDays, subMonths, format } from 'date-fns';

const queryClient = new QueryClient();

function AppContent() {
  const [activePage, setActivePage] = useState<'dashboard' | 'configuration'>('dashboard');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // State lifted from Dashboard
  const [selectedStockList, setSelectedStockList] = useState<string>('');
  const [showLogs, setShowLogs] = useState(false);

  // Date Range State (default: last 1 month)
  const [dateRange, setDateRange] = useState<{ start: string; end: string }>({
    start: format(subMonths(new Date(), 1), 'yyyy-MM-dd'),
    end: format(new Date(), 'yyyy-MM-dd')
  });

  // Auto-collapse sidebar on mobile
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setIsSidebarCollapsed(true);
      }
    };

    // Initial check
    handleResize();

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

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

  const handleRunAnalysis = () => {
    if (selectedStockList) {
      runAnalysisMutation.mutate();
    }
  };

  // Fetch analysis runs to derive latest update time
  const { data: runs } = useQuery({
    queryKey: ['analysisRuns'],
    queryFn: analysisApi.getRuns,
    refetchInterval: 30000
  });

  const latestUpdate = {
    timestamp: runs?.find(r => r.stock_list_name === selectedStockList)?.timestamp
      ? new Date(runs.find(r => r.stock_list_name === selectedStockList)!.timestamp).getTime() / 1000
      : null
  };

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      <Sidebar
        activePage={activePage}
        onNavigate={setActivePage}
        isCollapsed={isSidebarCollapsed}
        onToggle={() => setIsSidebarCollapsed(!isSidebarCollapsed)}

        // New props for sidebar controls
        selectedStockList={selectedStockList}
        setSelectedStockList={setSelectedStockList}
        stockLists={stockLists}
        handleRunAnalysis={handleRunAnalysis}
        jobStatus={jobStatus}
        latestUpdate={latestUpdate}
        showLogs={showLogs}
        setShowLogs={setShowLogs}
        dateRange={dateRange}
        setDateRange={setDateRange}
      />

      <main className="flex-1 overflow-auto bg-secondary/30 flex flex-col">
        {activePage === 'dashboard' ? (
          <Dashboard
            selectedStockList={selectedStockList}
            showLogs={showLogs}
            setShowLogs={setShowLogs}
            dateRange={dateRange}
          />
        ) : (
          <Configuration />
        )}
      </main>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}

export default App;
