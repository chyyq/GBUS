import { createReadStream, existsSync, statSync } from "node:fs";
import { createServer } from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const PORT = Number(process.env.PORT || 4173);

const types = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".svg": "image/svg+xml"
};

function safePath(urlPath) {
  const decoded = decodeURIComponent(urlPath.split("?")[0]);
  const normalized = path.normalize(decoded).replace(/^(\.\.[/\\])+/, "");
  const requested = path.join(ROOT, normalized);
  if (!requested.startsWith(ROOT)) return path.join(ROOT, "index.html");
  if (existsSync(requested) && statSync(requested).isDirectory()) {
    return path.join(requested, "index.html");
  }
  return existsSync(requested) ? requested : path.join(ROOT, "index.html");
}

const server = createServer((request, response) => {
  const filePath = safePath(request.url || "/");
  const extension = path.extname(filePath);
  response.writeHead(200, {
    "Content-Type": types[extension] || "application/octet-stream",
    "Cache-Control": "no-store"
  });
  createReadStream(filePath).pipe(response);
});

server.listen(PORT, () => {
  console.log(`GBUS Quant Dashboard: http://localhost:${PORT}`);
});
