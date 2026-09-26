#!/usr/bin/env bash
# ==============================================================================
# Linguo // Security Gate & Secret Scanner
# Scans staged git files for potential secrets, API keys, and sensitive tokens
# Prevents sensitive variables from ever reaching GitHub
# ==============================================================================
set -euo pipefail

echo "🛡️  Running Linguo Secret Scanner Gate..."

# Patterns to detect
PATTERNS=(
    "AIza[0-9A-Za-z-_]{35}"                  # Google / Gemini API Keys
    "sk-[a-zA-Z0-9]{20,}"                   # OpenAI API Keys
    "ghp_[a-zA-Z0-9]{36}"                   # GitHub Personal Access Tokens
    "github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}" # GitHub Fine-Grained Tokens
    "BEGIN[[:space:]]+(RSA|OPENSSH|DSA|EC)?[[:space:]]*PRIVATE[[:space:]]+KEY" # Private Keys
    "xox[baprs]-[0-9a-zA-Z]{10,48}"         # Slack Tokens
    "AKIA[0-9A-Z]{16}"                      # AWS Access Key ID
)

FAIL=0

# Get list of staged files (or all tracked files if --all passed)
if [[ "${1:-}" == "--all" ]]; then
    FILES=$(git ls-files)
else
    FILES=$(git diff --cached --name-only --diff-filter=ACM || git ls-files)
fi

for pattern in "${PATTERNS[@]}"; do
    for file in $FILES; do
        if [[ -f "$file" ]] && [[ "$file" != "scripts/check_secrets.sh" ]] && [[ "$file" != ".gitleaks.toml" ]]; then
            if grep -E -n -I -q "$pattern" "$file" 2>/dev/null; then
                echo "🚨 [BLOCKED] Sensitive pattern detected in: $file"
                echo "   Pattern: $pattern"
                grep -E -n -I "$pattern" "$file" | head -n 3
                FAIL=1
            fi
        fi
    done
done

if [[ $FAIL -ne 0 ]]; then
    echo ""
    echo "❌ COMMIT REJECTED: Sensitive keys or tokens found!"
    echo "   Remove secrets before committing, or use environment variables."
    exit 1
fi

echo "✅ Security Gate: No sensitive keys or tokens detected. Safe to commit!"
exit 0
