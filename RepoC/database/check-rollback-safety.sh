#!/usr/bin/env bash
set -e

# ---------------------------------------------------------------------------
# Usage: check-rollback-safety.sh <liquibase_properties_file> [<repo_name>]
# Example: ./database/check-rollback-safety.sh ./database/eh/schema/liquibase-dev.properties RepoA
# ---------------------------------------------------------------------------

PROP_FILE="$1"
REPO_NAME="${2:-UnknownRepo}"

if [ -z "$PROP_FILE" ]; then
  echo "❌ Usage: $0 <liquibase_properties_file> [repo_name]"
  exit 1
fi

echo "🔍 [${REPO_NAME}] Checking rollback safety using: $PROP_FILE"

# --- Step 1. Detect unapplied changesets -----------------------------------
echo "▶ Running dry-run updateSQL..."
if ! liquibase --defaults-file="$PROP_FILE" updateSQL > /tmp/liquibase_updates.sql 2>&1; then
  echo "❌ Liquibase updateSQL failed — aborting rollback."
  cat /tmp/liquibase_updates.sql
  exit 1
fi

PENDING_COUNT=$(grep -c "UPDATE DATABASECHANGELOG" /tmp/liquibase_updates.sql || true)
if [ "$PENDING_COUNT" -gt 0 ]; then
  echo "⚠️  Detected $PENDING_COUNT unapplied changesets."
  echo "   This may indicate other repositories (e.g., RepoB) have newer DB changes."
  echo "   Please run your migration task first, then retry rollback."
  exit 1
fi

# --- Step 2. Ensure rollbackCount does not exceed this repo's executed changes ----
echo "▶ Checking latest executed changesets for [$REPO_NAME]..."
# Get total executed for this repo (match on filename or author pattern)
EXECUTED_REPO_COUNT=$(liquibase --defaults-file="$PROP_FILE" history \
  | grep -i "$REPO_NAME" | wc -l | tr -d ' ')

# If no matches, repo may not have applied anything yet
if [ "$EXECUTED_REPO_COUNT" -eq 0 ]; then
  echo "ℹ️  No executed changesets found for [$REPO_NAME]. Nothing to roll back."
  exit 1
fi

# If user passed COUNT via Taskfile (as env var)
ROLLBACK_COUNT="${COUNT:-1}"

if [ "$ROLLBACK_COUNT" -gt "$EXECUTED_REPO_COUNT" ]; then
  echo "❌ Rollback count ($ROLLBACK_COUNT) exceeds executed changes for [$REPO_NAME] ($EXECUTED_REPO_COUNT)."
  echo "   Reduce rollback count or verify changelog history."
  exit 1
fi

# --- Step 3. All good ------------------------------------------------------
echo "✅ [${REPO_NAME}] Database state is up-to-date and rollback count is valid."
exit 0
