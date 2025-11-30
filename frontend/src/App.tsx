import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { Configuration } from './pages/Configuration';

const queryClient = new QueryClient();

function App() {
  const [activePage, setActivePage] = useState<'dashboard' | 'configuration'>('dashboard');

  return (
    <QueryClientProvider client={queryClient}>
      <div className="flex h-screen bg-background text-foreground overflow-hidden">
        <Sidebar activePage={activePage} onNavigate={setActivePage} />

        <main className="flex-1 overflow-auto bg-secondary/30 flex flex-col">
          {activePage === 'dashboard' ? <Dashboard /> : <Configuration />}
        </main>
      </div>
    </QueryClientProvider>
  );
}

export default App;
