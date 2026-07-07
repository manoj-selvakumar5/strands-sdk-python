# Strands Agents + Langfuse on AC Runtime

## TL;DR - Quick Fixes

| Issue | Fix |
|-------|-----|
| ADOT conflicts with Langfuse | Set `DISABLE_ADOT_OBSERVABILITY: 'true'` |
| Token counts inflated | Filter to only `"chat"` spans in Langfuse |
| Cache tokens break costs | Handle `cache_read_input_tokens` separately |

---

## Original Slack Comment

> If you deploy on AC Runtime, just beware that you have to disable ADOT on the runtime resource:
> ```yaml
> EnvironmentVariables:
>   DISABLE_ADOT_OBSERVABILITY: 'true'
> ```
> Other than that, it works like a charm except:
> - Span naming in Strands leads to too many tokens being noted in Langfuse
> - Prompt caching in Strands also breaks the logic for token consumption in Langfuse
>
> This was at least true in Langfuse 1.137.0

---

## Issue Breakdown

### 1. ADOT Conflict

**Problem:** AC Runtime has AWS Distro for OpenTelemetry (ADOT) built-in. Strands SDK has its own OpenTelemetry tracing. Running both causes duplicate traces and metric conflicts.

**Solution:**
```yaml
EnvironmentVariables:
  DISABLE_ADOT_OBSERVABILITY: 'true'
```

**How it works:**

1. AC Runtime has ADOT baked in - it auto-instruments and exports traces
2. Strands SDK has its own OpenTelemetry in `src/strands/telemetry/` - you control where it exports via:
   - `OTEL_EXPORTER_OTLP_ENDPOINT` (env var)
   - `StrandsTelemetry().setup_otlp_exporter()` (code)

By disabling ADOT, you avoid two competing OTEL systems fighting over trace context, and your Strands traces flow cleanly to Langfuse.

> **Caveat:** This disables AC Runtime's ADOT but keeps Strands SDK's OpenTelemetry active. However, it may also disable other AC Runtime telemetry you want. Test to confirm the behavior matches your expectations.

---

### 2. Token Double-Counting

**Problem:** Strands creates nested spans that each report token counts:

```
invoke_agent              <- Reports accumulated tokens (e.g., 3000)
├── execute_event_loop_cycle
│   └── chat              <- Reports tokens (e.g., 1000)
├── execute_event_loop_cycle
│   └── chat              <- Reports tokens (e.g., 1000)
└── execute_event_loop_cycle
    └── chat              <- Reports tokens (e.g., 1000)
```

If Langfuse sums ALL spans: 3000 + 1000 + 1000 + 1000 = 6000 (wrong)

**Solution:** Configure Langfuse to only count tokens from `"chat"` spans (the leaf nodes), not parent spans like `invoke_agent`.

---

### 3. Cache Token Handling

**Problem:** Strands reports cache tokens as separate attributes:
- `gen_ai.usage.cache_read_input_tokens` - tokens read from cache (90% cheaper)
- `gen_ai.usage.cache_write_input_tokens` - tokens written to cache

Langfuse v1.137.0 may not recognize these, leading to:
- Underreporting (ignoring cache tokens)
- Wrong costs (applying standard pricing to cache tokens)
- Double-counting (adding cache tokens to regular tokens)

**Solution:** Handle cache token attributes separately in Langfuse cost calculations, or upgrade to a newer Langfuse version that supports them.

---

## Technical Reference

<details>
<summary>Span Attributes (click to expand)</summary>

Each `"chat"` span includes:
```
gen_ai.usage.input_tokens
gen_ai.usage.output_tokens
gen_ai.usage.total_tokens
gen_ai.usage.cache_read_input_tokens   (optional)
gen_ai.usage.cache_write_input_tokens  (optional)
```

</details>

<details>
<summary>Strands SDK Files</summary>

| File | Purpose |
|------|---------|
| `src/strands/telemetry/tracer.py` | Span creation, token attributes |
| `src/strands/telemetry/metrics.py` | Metrics collection |
| `src/strands/types/event_loop.py` | `Usage` TypedDict definition |
| `src/strands/telemetry/config.py` | OTLP exporter setup |

</details>

<details>
<summary>Environment Variables</summary>

```bash
# Disable ADOT on AC Runtime
DISABLE_ADOT_OBSERVABILITY=true

# Use latest OpenTelemetry semantic conventions
OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental
```

</details>

---

## Version Info

- **Reported in:** Langfuse v1.137.0
- **Strands SDK:** Uses OpenTelemetry v1.37 semantic conventions
