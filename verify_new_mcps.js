import { execSync } from 'child_process';

const names = ["git", "filesystem", "chrome-devtools", "axiom", "arize-phoenix"];
const patterns = [
  "@modelcontextprotocol/server-{name}",
  "mcp-server-{name}",
  "{name}-mcp-server",
  "{name}-mcp"
];

const results = {};

for (const name of names) {
  results[name] = "NOT_FOUND";
  for (const pattern of patterns) {
    const pkg = pattern.replace("{name}", name);
    try {
      execSync(`npm view ${pkg} name --registry=https://registry.npmjs.org/`, { stdio: 'ignore' });
      results[name] = pkg;
      break;
    } catch (err) {}
  }
}

console.log(JSON.stringify(results, null, 2));
