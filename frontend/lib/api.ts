export async function api<T = Record<string, unknown>>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, { ...options, headers: { 'Content-Type': 'application/json', ...options?.headers }, cache: 'no-store' });
  const data = await response.json().catch(() => ({ detail: 'Backend unavailable. Start the Python service.' }));
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Invalid request. Check your inputs.');
  return data;
}
export const money = (value?: number | null) => value == null ? '—' : new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(value);
export const number = (value?: number | null, digits = 2) => value == null ? '—' : value.toFixed(digits);
