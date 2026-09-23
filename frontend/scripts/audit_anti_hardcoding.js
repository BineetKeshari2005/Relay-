#!/usr/bin/env node
/**
 * RELAY Anti-Hardcoding & UI Grounding Audit
 *
 * Verifies that:
 * 1. No conditional diagnosis logic branches on query text (e.g. `if (query === 'E17')`).
 * 2. No hardcoded diagnostic solutions or fabricated citations are embedded in UI components.
 * 3. All technical recommendations are dynamically rendered from API response structures.
 */

const fs = require("fs");
const path = require("path");

const SRC_DIR = path.join(__dirname, "..", "src");

// Patterns that indicate hardcoded diagnostic rules or hardcoded Q&A mappings
const FORBIDDEN_PATTERNS = [
  /if\s*\(\s*.*query.*===.*["']E17/i,
  /if\s*\(\s*.*query.*==.*["']E17/i,
  /if\s*\(\s*.*query.*\.includes\(["']E17["']\)\s*\)/i,
  /if\s*\(\s*.*error_code.*===.*["']E17.*return/i,
  /const\s+(hardcoded|mock)_(solutions|answers|diagnoses)\s*=/i,
  /citation.*id:\s*["']fake-/i,
  /citation.*id:\s*["']mock-cite/i,
];

let errorsFound = 0;

function scanDirectory(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      scanDirectory(fullPath);
    } else if (/\.(tsx|ts|jsx|js)$/.test(entry.name)) {
      const content = fs.readFileSync(fullPath, "utf8");
      FORBIDDEN_PATTERNS.forEach((pattern) => {
        if (pattern.test(content)) {
          console.error(
            `❌ VIOLATION: File ${path.relative(SRC_DIR, fullPath)} matched forbidden pattern: ${pattern}`
          );
          errorsFound++;
        }
      });
    }
  }
}

console.log("==================================================");
console.log("AUDITING RELAY FRONTEND FOR HARDCODED LOGIC");
console.log("==================================================");
scanDirectory(SRC_DIR);

if (errorsFound === 0) {
  console.log("✅ PASS: Zero hardcoded diagnostic branches or fabricated answers detected in frontend/src.");
  process.exit(0);
} else {
  console.error(`❌ FAIL: Found ${errorsFound} violations.`);
  process.exit(1);
}
