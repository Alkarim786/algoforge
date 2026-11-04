import { cpSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const target = join(root, "public", "monaco", "vs");

rmSync(target, { recursive: true, force: true });
cpSync(join(root, "node_modules", "monaco-editor", "min", "vs"), target, { recursive: true });
console.log(`Copied Monaco to ${target}`);
