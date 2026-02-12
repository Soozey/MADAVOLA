import { execSync } from "node:child_process";
import { readdirSync, statSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { brotliCompressSync, gzipSync } from "node:zlib";

const projectRoot = process.cwd();
const webDir = join(projectRoot, "apps", "web");
const distAssetsDir = join(webDir, "dist", "assets");

const JS_GZIP_BUDGET_KB = 180;
const COLD_START_GZIP_BUDGET_KB = 220;

function bytesToKb(bytes) {
  return bytes / 1024;
}

function listAssetFiles() {
  const entries = readdirSync(distAssetsDir, { withFileTypes: true });
  return entries
    .filter((entry) => entry.isFile())
    .map((entry) => entry.name)
    .sort((a, b) => a.localeCompare(b));
}

function getAssetStats(assetName) {
  const fullPath = join(distAssetsDir, assetName);
  const content = readFileSync(fullPath);
  const rawBytes = statSync(fullPath).size;
  const gzipBytes = gzipSync(content, { level: 9 }).length;
  const brotliBytes = brotliCompressSync(content).length;
  return { assetName, rawBytes, gzipBytes, brotliBytes };
}

function formatKb(bytes) {
  return `${bytesToKb(bytes).toFixed(2)} KB`;
}

function runBuild() {
  execSync("npm run build", { cwd: webDir, stdio: "inherit" });
}

function compareFileLists(before, after) {
  if (before.length !== after.length) return false;
  return before.every((value, index) => value === after[index]);
}

console.log("Building apps/web (pass 1)...");
runBuild();
const firstBuildFiles = listAssetFiles();

console.log("Building apps/web (pass 2, cache stability check)...");
runBuild();
const secondBuildFiles = listAssetFiles();

const cacheStable = compareFileLists(firstBuildFiles, secondBuildFiles);
if (!cacheStable) {
  console.error("Cache stability check failed: asset filenames changed between identical builds.");
  process.exit(1);
}

const stats = secondBuildFiles.map(getAssetStats);
const jsStats = stats.filter((s) => s.assetName.endsWith(".js"));
const cssStats = stats.filter((s) => s.assetName.endsWith(".css"));

const largestJsGzip = jsStats.reduce((max, s) => Math.max(max, s.gzipBytes), 0);
if (bytesToKb(largestJsGzip) > JS_GZIP_BUDGET_KB) {
  console.error(
    `Largest JS gzip size ${formatKb(largestJsGzip)} exceeds budget ${JS_GZIP_BUDGET_KB} KB.`
  );
  process.exit(1);
}

const coldStartGzip = [...jsStats, ...cssStats].reduce((sum, s) => sum + s.gzipBytes, 0);
if (bytesToKb(coldStartGzip) > COLD_START_GZIP_BUDGET_KB) {
  console.error(
    `Cold-start gzip total ${formatKb(coldStartGzip)} exceeds budget ${COLD_START_GZIP_BUDGET_KB} KB.`
  );
  process.exit(1);
}

console.log("\nBundle summary (apps/web/dist/assets):");
for (const asset of stats) {
  console.log(
    `${asset.assetName.padEnd(34)} raw=${formatKb(asset.rawBytes).padStart(9)} gzip=${formatKb(
      asset.gzipBytes
    ).padStart(9)} brotli=${formatKb(asset.brotliBytes).padStart(9)}`
  );
}

console.log("\nChecks passed:");
console.log(`- cache stability between 2 identical builds: OK`);
console.log(`- largest JS gzip <= ${JS_GZIP_BUDGET_KB} KB: OK (${formatKb(largestJsGzip)})`);
console.log(
  `- cold-start gzip JS+CSS <= ${COLD_START_GZIP_BUDGET_KB} KB: OK (${formatKb(coldStartGzip)})`
);
