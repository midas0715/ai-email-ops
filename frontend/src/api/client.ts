import { loadSession } from "../auth/token";

const BASE_URL: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

// The auth code registers a function here that logs the user out
let unauthorizedHandler: (() => void) | null = null;

export function setUnauthorizedHandler(handler: (() => void) | null): void {
  unauthorizedHandler = handler;
}

interface RequestOptions {
  method?: string;
  json?: unknown; // sent as JSON
  form?: Record<string, string>; // sent as a form (the login routes want this)
  auth?: boolean; // set to false for login and register
  formData?: FormData; // sent as a file upload
}

// FastAPI sends {"detail": "text"} or, for invalid input, {"detail": [{"msg": ...}]}
function messageFromBody(body: unknown, fallback: string): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((item) =>
          item && typeof item === "object" && "msg" in item
            ? String((item as { msg: unknown }).msg)
            : "Invalid input",
        )
        .join(". ");
    }
  }
  return fallback;
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {};
  let body: BodyInit | undefined;

  if (options.json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(options.json);
  } else if (options.form) {
    body = new URLSearchParams(options.form); // the browser sets the content type itself
  } else if (options.formData) {
    body = options.formData; // the browser adds the multipart headers itself
  }

  const sendToken = options.auth !== false;
  const session = sendToken ? loadSession() : null;
  if (session) headers["Authorization"] = `Bearer ${session.token}`;

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method: options.method ?? "GET",
      headers,
      body,
    });
  } catch {
    throw new ApiError(0, "Cannot reach the server. Is the API running?");
  }

  const text = await response.text();
  let data: unknown;
  try {
    data = text ? JSON.parse(text) : undefined;
  } catch {
    data = undefined;
  }

  if (!response.ok) {
    if (response.status === 401 && sendToken) unauthorizedHandler?.();
    throw new ApiError(response.status, messageFromBody(data, `Request failed (${response.status})`));
  }
  return data as T;
}