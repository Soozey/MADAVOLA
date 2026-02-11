import axios, { AxiosInstance } from "axios";
import { useAuthStore } from "../stores/authStore";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Intercepteur pour ajouter le token
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Intercepteur pour gérer les erreurs
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expiré, déconnexion
      useAuthStore.getState().logout();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default apiClient;

export async function getRoleReferential() {
  const { data } = await apiClient.get("/roles/referential");
  return data;
}

export async function assignRole(actorId: number, role: string) {
  const { data } = await apiClient.post(`/admin/actors/${actorId}/roles`, { role });
  return data;
}

export async function getActorRoles(actorId: number) {
  const { data } = await apiClient.get(`/admin/actors/${actorId}/roles`);
  return data;
}

export async function updateRole(roleId: number, payload: { status?: string; valid_from?: string; valid_to?: string }) {
  const { data } = await apiClient.patch(`/admin/roles/${roleId}`, payload);
  return data;
}

export async function deleteRole(roleId: number) {
  await apiClient.delete(`/admin/roles/${roleId}`);
}

// Config système
export async function listConfigs(key?: string) {
  const { data } = await apiClient.get("/admin/config", { params: key ? { key } : undefined });
  return data;
}

export async function createConfig(payload: { key: string; value?: string; description?: string }) {
  const { data } = await apiClient.post("/admin/config", payload);
  return data;
}

export async function updateConfig(configId: number, payload: { value?: string; description?: string }) {
  const { data } = await apiClient.patch(`/admin/config/${configId}`, payload);
  return data;
}

export async function deleteConfig(configId: number) {
  await apiClient.delete(`/admin/config/${configId}`);
}
