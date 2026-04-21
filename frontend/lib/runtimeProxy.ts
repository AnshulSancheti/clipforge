function backendBaseUrl() {
  if (process.env.INTERNAL_API_URL) return process.env.INTERNAL_API_URL.replace(/\/+$/, "");
  if (process.env.BACKEND_URL) return process.env.BACKEND_URL.replace(/\/+$/, "");

  // Strip /api suffix only if the result is non-empty
  const stripped = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/api\/?$/, "").replace(/\/+$/, "");
  if (stripped) return stripped;

  return "http://localhost:8000";
}

export async function proxyToBackend(
  request: Request,
  pathParts: string[] | undefined,
  prefix: "api" | "storage",
) {
  try {
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
      init.body = request.body;
      (init as RequestInit & { duplex: string }).duplex = "half";
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
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown proxy error";
    return new Response(JSON.stringify({ detail: `Proxy error: ${message}` }), {
      status: 502,
      headers: { "content-type": "application/json" },
    });
  }
}
