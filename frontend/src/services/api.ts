import axios from 'axios';

// Use the current hostname so it works both locally and from other devices
const API_BASE_URL = `http://${window.location.hostname}:8000/api`;

export const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export interface StockList {
    filename: string;
    count: number;
    preview: string[];
    content?: string;
}

export interface JobStatus {
    job_id: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    progress: number;
    error?: string;
    start_time?: string;
    end_time?: string;
}

export const stocksApi = {
    list: async () => {
        const response = await api.get<string[]>('/stocks/');
        return response.data;
    },
    get: async (filename: string) => {
        const response = await api.get<StockList>(`/stocks/${filename}`);
        return response.data;
    },
    create: async (name: string, content: string, extension: string = '.tab') => {
        const response = await api.post('/stocks/', { name, content, extension });
        return response.data;
    },
    update: async (filename: string, content: string) => {
        const response = await api.put(`/stocks/${filename}`, { content });
        return response.data;
    },
    delete: async (filename: string) => {
        const response = await api.delete(`/stocks/${filename}`);
        return response.data;
    },
};

export const analysisApi = {
    run: async (stock_list_file: string, end_date?: string) => {
        const response = await api.post<JobStatus>('/analysis/run', { stock_list_file, end_date });
        return response.data;
    },
    getStatus: async () => {
        const response = await api.get<JobStatus | null>('/analysis/status/current');
        return response.data;
    },
    listFiles: async (stock_list?: string) => {
        const params = stock_list ? { stock_list } : {};
        const response = await api.get<string[]>('/analysis/results/files', { params });
        return response.data;
    },
    getFileContent: async (filename: string) => {
        const response = await api.get<any[]>('/analysis/results/content/' + filename);
        return response.data;
    },
    getLatestUpdate: async (stock_list: string) => {
        const response = await api.get<{ timestamp: number | null }>('/analysis/results/latest_update', { params: { stock_list } });
        return response.data;
    },
    getLogs: async (lines: number = 50) => {
        const response = await api.get<{ logs: string[] }>('/analysis/logs', { params: { lines } });
        return response.data;
    },
    getPriceData: async (ticker: string, interval: string = '1d', days: number = 60) => {
        const response = await api.get<any[]>(`/analysis/price_data/${ticker}`, { params: { interval, days } });
        return response.data;
    },
    getPriceHistory: async (ticker: string, interval: string) => {
        const response = await api.get<any[]>(`/analysis/price_history/${ticker}/${interval}`);
        return response.data;
    },
};
