import { SharedDAL, HttpAdapter } from "../../../shared/dal";

// Native Fetch Adapter for Shared DAL
class NativeAdapter implements HttpAdapter {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}/${endpoint}`);
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    return response.json();
  }

  async post<T>(endpoint: string, body: unknown): Promise<T> {
    const response = await fetch(`${this.baseUrl}/${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    return response.json();
  }
}

export const api = new SharedDAL(
  new NativeAdapter(process.env.API_URL || "http://localhost:8000/api")
);
