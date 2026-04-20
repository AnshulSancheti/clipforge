function backendBaseUrl() {
  const raw =
    process.env.INTERNAL_API_URL ||
    process.env.BACKEND_URL ||
    process.env.NEXT_PUBLIC_API_URL?.replace(/\/api\/?$/, "") ||
    "http://localhost:8000";

  return raw.replace(/\/+$/, "");
}

export async function proxyToBackend(
  request: Request,
  pathParts: string[] | undefined,
  prefix: "api" | "storage",
) {
  const incomingUrl = new URL(request.url);
  const path = pathParts?.join("/") || "";
  const targetUrl = new URL(`/${prefix}/${path}${incomingUrl.search}`, backendBaseUrl());

  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("content-length");

  const init: RequestInit = {
    method: request.method,
    headers,
    redirect: "manual",
  };

  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.arrayBuffer();
  }

  const response = await fetch(targetUrl, init);
  const responseHeaders = new Headers(response.headers);
  responseHeaders.delete("content-encoding");
  responseHeaders.delete("content-length");

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders,
  });
}
