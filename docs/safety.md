# Safety & Limitations

This document covers known risks, limitations, and best practices for using Neural Memory safely.

## Known Risks

### 1. Memory Poisoning

**Risk Level:** HIGH

**Description:** Incorrect, malicious, or outdated information stored in memory can propagate to future recalls, leading to incorrect conclusions or actions.

**Examples:**
- Storing wrong API endpoint: future code may use wrong URL
- Incorrect person attribution: "Bob said X" when Alice said it
- Outdated information: old phone numbers, deprecated APIs

**Mitigations:**
```bash
# Verify before storing
nmem check "Bob's phone: 555-1234"

# Use tags to mark source/confidence
nmem remember "Bob's phone: 555-1234" -t unverified -t needs-confirmation

# Review health periodically
nmem brain health
```

**Best Practices:**
- Always verify critical information before storing
- Use tags to indicate confidence level: `verified`, `unverified`, `needs-review`
- Include source attribution: "Per email from Bob on 2024-02-04..."
- Periodically review and clean up old memories

---

### 2. Stale Memory

**Risk Level:** MEDIUM

**Description:** Old memories become outdated but are still returned in queries, leading to use of obsolete information.

**Examples:**
- Old project decisions that have since changed
- Former employee contact information
- Deprecated API versions
- Changed passwords or credentials

**Mitigations:**
```bash
# Check memory freshness
nmem stats

# Get only fresh context
nmem context --fresh-only

# Review brain health
nmem brain health

# Recall shows age warnings automatically
nmem recall "Bob's contact"
# Output includes: ⚠️ STALE: This memory is 180 days old - verify before using
```

**Freshness Levels:**
| Level | Age | Indicator | Action |
|-------|-----|-----------|--------|
| Fresh | < 7 days | 🟢 | Safe to use |
| Recent | 7-30 days | 🟢 | Generally safe |
| Aging | 30-90 days | 🟡 | Consider verifying |
| Stale | 90-365 days | 🟠 | Verify before using |
| Ancient | > 365 days | 🔴 | Likely outdated |

---

### 3. Privacy Leak

**Risk Level:** HIGH

**Description:** Sensitive information (API keys, passwords, PII) stored in memory can be accidentally exposed through exports, sharing, or logs.

**Examples:**
- API keys stored in memory: `nmem remember "API_KEY=sk-xxx"`
- Database credentials in connection strings
- Personal information (SSN, credit cards)
- Private keys and tokens

**Mitigations:**
```bash
# Check content before storing
nmem check "My AWS_SECRET_KEY=xxx"
# Output: ⚠️ SENSITIVE CONTENT DETECTED

# Auto-redact sensitive content
nmem remember "Config: API_KEY=sk-xxx123" --redact
# Stores: "Config: API_KEY=[REDACTED]"

# Export without sensitive content
nmem brain export --exclude-sensitive -o safe-backup.json

# Scan imports for sensitive content
nmem brain import untrusted.json --scan
```

**Detected Sensitive Patterns:**
- API keys and secrets (`api_key=`, `secret=`)
- Passwords (`password=`, `pwd=`)
- AWS credentials (`aws_access_key_id`, `aws_secret_access_key`)
- Database URLs with credentials
- Private keys (PEM format)
- JWT tokens
- Credit card numbers
- Social Security Numbers

---

### 4. Over-reliance

**Risk Level:** MEDIUM

**Description:** Blindly trusting memory system output without verification can lead to errors, especially for critical decisions.

**Examples:**
- Using remembered code without reviewing
- Trusting old configuration values
- Acting on potentially outdated information

**Mitigations:**
```bash
# Always check confidence scores
nmem recall "critical config" --json | jq '.confidence'

# Set minimum confidence threshold
nmem recall "important decision" --min-confidence 0.7

# Check memory age
nmem recall "api endpoint" --show-age
```

**Best Practices:**
- Treat memory as "hints" not "facts" for critical operations
- Always verify security-sensitive information
- Use confidence thresholds for automated systems
- Cross-reference with authoritative sources for important data

---

## Security Best Practices

### 1. Data Classification

Classify what should and shouldn't be stored:

**DO Store:**
- Project decisions and rationale
- Meeting notes (non-confidential)
- Code patterns and solutions
- Error resolutions
- Workflow documentation

**DON'T Store:**
- Passwords and API keys
- Personal identification numbers
- Credit card or financial data
- Private encryption keys
- Medical or legal information

### 2. Brain Isolation

Use separate brains for different security contexts:

```bash
# Create isolated brains
nmem brain create work-public      # Safe to share
nmem brain create work-internal    # Internal only
nmem brain create personal         # Never share

# Switch between them
nmem brain use work-public
```

### 3. Export Safety

Always use `--exclude-sensitive` when sharing:

```bash
# Safe export
nmem brain export --exclude-sensitive -o shareable.json

# Check before sharing
nmem brain health --name work-public
```

### 4. Regular Audits

Periodically review brain health:

```bash
# Weekly health check
nmem brain health

# Review stale memories
nmem stats

# Clean up if needed
nmem brain delete old-project
```

---

## System Limitations

### 1. No Encryption at Rest

**Current State:** Memory data is stored as plain JSON files.

**Implication:** Anyone with file system access can read memories.

**Workaround:**
- Use encrypted file system (BitLocker, FileVault, LUKS)
- Store data directory on encrypted volume

### 2. No Access Control

**Current State:** No authentication or authorization system.

**Implication:** All brains are accessible to anyone with CLI access.

**Workaround:**
- Use file system permissions
- Separate brains per user
- Use server mode with authentication (future)

### 3. No Automatic Cleanup

**Current State:** Memories are not automatically deleted or archived.

**Implication:** Data grows unbounded; stale memories accumulate.

**Workaround:**
- Manual periodic cleanup
- Use `--fresh-only` flag for context
- Export/reimport to clean up

### 4. No Contradiction Detection

**Current State:** Conflicting memories can coexist.

**Implication:** May get inconsistent results depending on query.

**Workaround:**
- Use tags to mark superseded information
- Include timestamps in memories
- Manually resolve conflicts

### 5. Retrieval Accuracy

**Current State:** Spreading activation may not always find the most relevant memories.

**Implication:** Important memories might be missed; irrelevant ones returned.

**Workaround:**
- Use specific queries
- Try different depth levels
- Use tags for better organization

---

## Incident Response

### If Sensitive Data Was Stored

1. **Identify:** Find the affected memories
   ```bash
   nmem brain health
   ```

2. **Remove:** Delete the brain or affected data
   ```bash
   nmem brain delete compromised-brain --force
   ```

3. **Rotate:** Change any exposed credentials immediately

4. **Audit:** Check exports and shared data

### If Brain Was Shared Accidentally

1. **Revoke:** Remove shared files immediately

2. **Assess:** Determine what was exposed
   ```bash
   nmem check "$(cat shared-file.json)"
   ```

3. **Rotate:** Change any potentially exposed credentials

4. **Notify:** Inform affected parties if PII was involved

---

## Recommendations by Use Case

### Personal Use
- Use default local storage
- Enable sensitive content warnings
- Regular backups with `--exclude-sensitive`

### Team Use
- Separate brains per project/sensitivity level
- Never share brains with sensitive content
- Use `brain health` before sharing

### Automated/CI Use
- Always set `--min-confidence` threshold
- Never store credentials in memory
- Use environment variables for secrets
- Log confidence scores for audit

### Production/Enterprise
- Wait for server mode with authentication
- Use encrypted storage backend
- Implement access logging
- Regular security audits
