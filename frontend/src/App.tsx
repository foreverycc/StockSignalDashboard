import { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider, useQuery, useMutation } from '@tanstack/react-query';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { Configuration } from './pages/Configuration';
import { analysisApi, stocksApi } from './services/api';

const queryClient = new QueryClient();

function AppContent() {
  const [activePage, setActivePage] = useState<'dashboard' | 'configuration'>('dashboard');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // State lifted from Dashboard
  const [selectedStockList, setSelectedStockList] = useState<string>('');
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

  const handleRunAnalysis = () => {
    if (selectedStockList) {
      runAnalysisMutation.mutate();
    }
  };

  // Fetch latest update time
  const { data: latestUpdate } = useQuery({
    queryKey: ['latestUpdate', selectedStockList],
    queryFn: () => selectedStockList ? analysisApi.getLatestUpdate(selectedStockList) : null,
    enabled: !!selectedStockList
  });

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
      />

      <main className="flex-1 overflow-auto bg-secondary/30 flex flex-col">
        {activePage === 'dashboard' ? (
          <Dashboard
            selectedStockList={selectedStockList}
            setSelectedStockList={setSelectedStockList}
            showLogs={showLogs}
            setShowLogs={setShowLogs}
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
