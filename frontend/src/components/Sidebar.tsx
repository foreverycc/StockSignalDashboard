import React from 'react';
import { LayoutDashboard, Settings, Activity } from 'lucide-react';
import { cn } from '../utils/cn';

interface SidebarProps {
    activePage: 'dashboard' | 'configuration';
    onNavigate: (page: 'dashboard' | 'configuration') => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activePage, onNavigate }) => {
    return (
        <div className="w-64 bg-card border-r border-border h-screen flex flex-col">
            <div className="p-6 border-b border-border">
                <h1 className="text-xl font-bold flex items-center gap-2 text-primary">
                    <Activity className="w-6 h-6" />
                    Stock Signal
                </h1>
            </div>

            <nav className="flex-1 p-4 space-y-2">
                <button
                    onClick={() => onNavigate('dashboard')}
                    className={cn(
                        "w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors",
                        activePage === 'dashboard'
                            ? "bg-primary/10 text-primary font-medium"
                            : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    )}
                >
                    <LayoutDashboard className="w-5 h-5" />
                    Dashboard
                </button>

                <button
                    onClick={() => onNavigate('configuration')}
                    className={cn(
                        "w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors",
                        activePage === 'configuration'
                            ? "bg-primary/10 text-primary font-medium"
                            : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    )}
                >
                    <Settings className="w-5 h-5" />
                    Configuration
                </button>
            </nav>

            <div className="p-4 border-t border-border text-xs text-muted-foreground text-center">
                v1.0.0 Production Ready
            </div>
        </div>
    );
};
