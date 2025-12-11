import axios from 'axios';

// A single base URL for all API calls.
// Using a relative URL ensures that requests are sent to the same host that served the frontend,
// which will be correctly routed by the Ingress controller in Kubernetes.
const API_BASE_URL = '/';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Add a request interceptor to include the auth token if it exists
apiClient.interceptors.request.use(config => {
    const token = localStorage.getItem('authToken');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
}, error => {
    return Promise.reject(error);
});


// Patients & Vitals API
export const getPatients = async () => {
    const response = await apiClient.get('/api/patients');
    return response.data;
};

export const getPatientById = async (patientId) => {
    const response = await apiClient.get(`/api/patients/${patientId}`);
    return response.data;
};

export const getPatientVitals = async (patientId) => {
    const response = await apiClient.get(`/api/patients/${patientId}/vitals`);
    return response.data;
};

export const getPatientVitalsHistory = async (patientId, hours = 24) => {
    const response = await apiClient.get(`/api/patients/${patientId}/vitals/history`, {
        params: { hours }
    });
    return response.data;
};

// Alerts API
export const getAlerts = async () => {
    const response = await apiClient.get('/api/alerts');
    return response.data;
};

export const getPatientAlerts = async (patientId) => {
    const response = await apiClient.get(`/api/alerts/${patientId}`);
    return response.data;
};

// Summarizer API
export const getSummaries = async () => {
    const response = await apiClient.get('/api/summaries');
    return response.data;
};

export const getPatientSummary = async (patientId) => {
    const response = await apiClient.get(`/api/summaries/${patientId}`);
    return response.data;
};

export const getModelInfo = async () => {
    const response = await apiClient.get('/api/model/info');
    return response.data;
};

export const triggerSummary = async (patientId) => {
    const response = await apiClient.post('/api/model/trigger-summary', { patientId });
    return response.data;
};

// Auth API
export const authApi = {
    login: async (username, password) => {
        const response = await apiClient.post('/api/auth/login', { username, password });
        if (response.data.access_token) {
            localStorage.setItem('authToken', response.data.access_token);
        }
        return response.data;
    },
    logout: async () => {
        const response = await apiClient.post('/api/auth/logout');
        localStorage.removeItem('authToken');
        return response.data;
    },
    verify: async () => {
        const response = await apiClient.get('/api/auth/verify');
        return response.data;
    },
    getMe: async () => {
        const response = await apiClient.get('/api/auth/me');
        return response.data;
    }
};

// WebSocket connection for real-time vitals
export const createVitalsWebSocket = (patientId, onMessage, onError) => {
    // Construct a relative WebSocket URL
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/vitals/${patientId}`;
    
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        onMessage(data);
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        if (onError) onError(error);
    };

    return ws;
};

// Health check
export const healthCheck = async () => {
    try {
        const [vitals, alerts, summarizer, auth] = await Promise.all([
            apiClient.get('/health-vitals'),
            apiClient.get('/health-alerts'),
            apiClient.get('/health-summarizer'),
            apiClient.get('/health-auth')
        ]);
        return {
            vitals: vitals.status === 200,
            alerts: alerts.status === 200,
            summarizer: summarizer.status === 200,
            auth: auth.status === 200,
        };
    } catch (error) {
        console.error('Health check failed:', error);
        return { vitals: false, alerts: false, summarizer: false, auth: false };
    }
};
