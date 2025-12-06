import React from 'react';
import { LayoutDashboard, Settings, Activity, ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '../utils/cn';

interface SidebarProps {
    activePage: 'dashboard' | 'configuration';
    onNavigate: (page: 'dashboard' | 'configuration') => void;
    isCollapsed: boolean;
    onToggle: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activePage, onNavigate, isCollapsed, onToggle }) => {
    return (
        <div
            className={cn(
                "bg-card border-r border-border h-screen flex flex-col transition-all duration-300 ease-in-out relative",
                isCollapsed ? "w-20" : "w-64"
            )}
        >
            {/* Toggle Button */}
            <button
                onClick={onToggle}
                className="absolute -right-3 top-9 bg-primary text-primary-foreground rounded-full p-1 shadow-md hover:bg-primary/90 transition-colors z-50"
            >
                {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </button>

            <div className={cn("p-6 border-b border-border flex items-center", isCollapsed ? "justify-center px-2" : "")}>
                <div className="flex items-center gap-2 text-primary overflow-hidden whitespace-nowrap">
                    <Activity className="w-6 h-6 shrink-0" />
                    <span className={cn("font-bold text-xl transition-opacity duration-300", isCollapsed ? "opacity-0 w-0" : "opacity-100")}>
                        Stock Signal
                    </span>
                </div>
            </div>

            <nav className="flex-1 p-4 space-y-2">
                <button
                    onClick={() => onNavigate('dashboard')}
                    className={cn(
                        "w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors overflow-hidden whitespace-nowrap",
                        activePage === 'dashboard'
                            ? "bg-primary/10 text-primary font-medium"
                            : "text-muted-foreground hover:bg-muted hover:text-foreground",
                        isCollapsed ? "justify-center px-2" : ""
                    )}
                    title={isCollapsed ? "Dashboard" : undefined}
                >
                    <LayoutDashboard className="w-5 h-5 shrink-0" />
                    <span className={cn("transition-opacity duration-300", isCollapsed ? "opacity-0 w-0" : "opacity-100")}>
                        Dashboard
                    </span>
                </button>

                <button
                    onClick={() => onNavigate('configuration')}
                    className={cn(
                        "w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors overflow-hidden whitespace-nowrap",
                        activePage === 'configuration'
                            ? "bg-primary/10 text-primary font-medium"
                            : "text-muted-foreground hover:bg-muted hover:text-foreground",
                        isCollapsed ? "justify-center px-2" : ""
                    )}
                    title={isCollapsed ? "Configuration" : undefined}
                >
                    <Settings className="w-5 h-5 shrink-0" />
                    <span className={cn("transition-opacity duration-300", isCollapsed ? "opacity-0 w-0" : "opacity-100")}>
                        Configuration
                    </span>
                </button>
            </nav>

            <div className="p-4 border-t border-border text-xs text-muted-foreground text-center overflow-hidden whitespace-nowrap">
                <span className={cn("transition-opacity duration-300", isCollapsed ? "opacity-0 hidden" : "opacity-100")}>
                    v1.0.0 Production Ready
                </span>
                {isCollapsed && <span className="text-[10px]">v1.0</span>}
            </div>
        </div>
    );
};
