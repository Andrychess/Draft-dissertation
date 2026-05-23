import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({ baseURL: API_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    if (error.response?.status === 401) {
      const refresh = localStorage.getItem("refresh_token");
      if (refresh && !error.config._retry) {
        error.config._retry = true;
        try {
          const { data } = await axios.post(`${API_URL}/api/auth/refresh`, {
            refresh_token: refresh,
          });
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          error.config.headers.Authorization = `Bearer ${data.access_token}`;
          return api.request(error.config);
        } catch {
          localStorage.clear();
        }
      }
    }
    return Promise.reject(error);
  }
);

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: "admin" | "teacher";
  is_active: boolean;
}

export const authApi = {
  login: (email: string, password: string) =>
    api.post("/api/auth/login", { email, password }),
};

export const usersApi = {
  list: () => api.get<User[]>("/api/users"),
  create: (data: object) => api.post("/api/users", data),
  update: (id: number, data: object) => api.put(`/api/users/${id}`, data),
  remove: (id: number) => api.delete(`/api/users/${id}`),
};

export const groupsApi = {
  list: () => api.get("/api/groups"),
  create: (data: { cipher: string; name: string }) => api.post("/api/groups", data),
};

export const templatesApi = {
  list: () => api.get("/api/templates"),
  get: (id: number) => api.get(`/api/templates/${id}`),
  create: (data: { name: string }) => api.post("/api/templates", data),
  update: (id: number, data: object) => api.put(`/api/templates/${id}`, data),
  remove: (id: number) => api.delete(`/api/templates/${id}`),
  addQuestion: (id: number, data: object) => api.post(`/api/templates/${id}/questions`, data),
  updateQuestion: (id: number, data: object) => api.put(`/api/questions/${id}`, data),
  deleteQuestion: (id: number) => api.delete(`/api/questions/${id}`),
};

export const sessionsApi = {
  list: () => api.get("/api/sessions"),
  create: (data: object) => api.post("/api/sessions", data),
  extend: (id: number, end_time: string) => api.put(`/api/sessions/${id}/extend`, { end_time }),
  finish: (id: number) => api.post(`/api/sessions/${id}/finish`),
  checkCode: (code: string) => api.get(`/api/sessions/join/${code}`),
  join: (data: object) => api.post("/api/sessions/join", data),
  questions: (id: number) => api.get(`/api/sessions/${id}/questions`),
  results: (id: number) => api.get(`/api/sessions/${id}/results`),
  exportCsv: (id: number) => api.get(`/api/sessions/${id}/export`, { responseType: "blob" }),
};

export const answersApi = {
  save: (data: object) => api.post("/api/answers/save", data),
  submit: (sheet_id: number) => api.post("/api/answers/submit", { sheet_id }),
};

export const resultsApi = {
  detail: (sheet_id: number) => api.get(`/api/results/${sheet_id}`),
  approve: (check_id: number) => api.put(`/api/results/${check_id}/approve`, {}),
  correct: (check_id: number, data: object) => api.put(`/api/results/${check_id}`, data),
};

export const studentApi = {
  results: (sheet_id: number) => api.get(`/api/student/results/${sheet_id}`),
  status: (sheet_id: number) => api.get(`/api/student/results/${sheet_id}/status`),
};

export const adminApi = {
  logs: (limit = 100) => api.get("/api/admin/logs", { params: { limit } }),
  settings: () => api.get("/api/admin/settings"),
  updateSettings: (data: object) => api.put("/api/admin/settings", data),
};
