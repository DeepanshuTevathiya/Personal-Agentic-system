const http = require("http");
const fs = require("fs");
const path = require("path");
const { URL } = require("url");

const uiRoot = __dirname;
const uiPort = Number(process.env.UI_PORT || 4173);
const apiOrigin = process.env.NEXUS_API_ORIGIN || "http://127.0.0.1:8000";
const types = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8" };

function sendFile(requestPath, response) {
  const requested = requestPath === "/" ? "/index.html" : requestPath;
  const filePath = path.resolve(uiRoot, `.${requested}`);
  if (!filePath.startsWith(uiRoot)) { response.writeHead(403).end("Forbidden"); return; }
  fs.readFile(filePath, (error, file) => {
    if (error) { response.writeHead(error.code === "ENOENT" ? 404 : 500).end("Not found"); return; }
    response.writeHead(200, { "Content-Type": types[path.extname(filePath)] || "application/octet-stream", "Cache-Control": "no-store" });
    response.end(file);
  });
}

function proxy(request, response) {
  const target = new URL(request.url.replace(/^\/api/, ""), apiOrigin);
  const upstream = http.request(target, { method: request.method, headers: { ...request.headers, host: target.host } }, upstreamResponse => {
    response.writeHead(upstreamResponse.statusCode || 502, upstreamResponse.headers);
    upstreamResponse.pipe(response);
  });
  upstream.on("error", () => { response.writeHead(502, { "Content-Type": "application/json" }); response.end(JSON.stringify({ detail: "Nexus API is unavailable. Start FastAPI on port 8000." })); });
  request.pipe(upstream);
}

http.createServer((request, response) => request.url.startsWith("/api/") ? proxy(request, response) : sendFile(new URL(request.url, "http://localhost").pathname, response))
  .listen(uiPort, () => console.log(`Nexus UI: http://127.0.0.1:${uiPort}`));
