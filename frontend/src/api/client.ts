import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

export async function healthCheck(): Promise<{ status: string; version: string }> {
  const { data } = await api.get("/health");
  return data;
}

export default api;
