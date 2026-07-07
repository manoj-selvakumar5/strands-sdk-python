# Strands Agents SDK: LTS & Security Vulnerability Handling

**Date:** 2026-02-12
**Context:** Research — understanding support policy and security practices

## Summary

No formal LTS policy exists. Only 1.x.x is supported. Security vulnerabilities are reported privately via AWS HackerOne or email. Dependabot runs daily for dependency scanning.

---

## Long-Term Support

### Supported Versions (from SECURITY.md)

| Version | Supported |
|---------|-----------|
| 1.x.x | Yes |
| < 1.0 | No |

### Key Facts

- **License:** Apache 2.0
- **Status:** "Production/Stable" (pyproject.toml classifier)
- **Python versions:** 3.10, 3.11, 3.12, 3.13
- **Maintained by:** AWS (`opensource@amazon.com`)
- **Versioning:** git tags via hatch-vcs
- **No published LTS timeline, EOL dates, or multi-version support windows**
- Only the current 1.x.x line receives patches

---

## Security Vulnerability Handling

### Reporting Process

Security vulnerabilities must be reported **privately** (not via public GitHub issues):

1. **Primary:** [AWS HackerOne VDP](https://hackerone.com/aws_vdp)
2. **Alternative:** Email aws-security@amazon.com
3. **Reference:** [AWS Vulnerability Reporting Page](http://aws.amazon.com/security/vulnerability-reporting/)

### Automated Dependency Scanning

Dependabot configured in `.github/dependabot.yml`:

- **pip dependencies** — scanned daily, up to 100 open PRs
- **github-actions** — scanned daily, up to 100 open PRs
- Commit prefix: `ci` (conventional commits)
- Dev dependencies (pytest) grouped together

### CI/CD Security

| Workflow | Purpose |
|----------|---------|
| `test-lint.yml` | Linting, formatting, type checks |
| `pr-and-push.yml` | Runs on PRs and pushes |
| `integration-test.yml` | Integration tests |

No dedicated SAST/DAST or CodeQL workflow visible in the repo.

### What's Not Documented

- No SLA for security patches
- No CVE disclosure timeline
- No security advisory process (beyond AWS VDP)
- No SBOM (Software Bill of Materials) generation
- No signed releases

---

## Summary Table

| Aspect | Detail |
|--------|--------|
| Supported versions | 1.x.x only |
| Vulnerability reporting | Private: HackerOne or aws-security@amazon.com |
| Dependency scanning | Dependabot daily (pip + GitHub Actions) |
| SAST/security scanning | Not visible in repo workflows |
| SLA for patches | Not documented |
| CVE disclosure process | Via AWS Vulnerability Disclosure Program |

## What Customers Really Mean When They Ask About LTS

When customers ask "What's the LTS story?", they're asking: **"Is it safe to bet our production workload on this?"** They want concrete commitments on maintenance duration, security response times, and version support windows.

### The 5 Questions Behind "LTS"

1. **"Will this SDK still be maintained in 2+ years?"** — Is AWS committed long-term? Is there a public roadmap? Could it be abandoned?
2. **"How fast will security patches be released?"** — What's the SLA for CVEs? Days, weeks, months? Is there a notification system?
3. **"Will breaking changes happen without warning?"** — Deprecation policy? How long are major versions supported after a new one ships?
4. **"Can I get enterprise support?"** — Paid support via AWS Enterprise Support? Or community-only (GitHub issues)?
5. **"Does it meet compliance requirements?"** — SBOM for supply chain audits? Signed releases? SOC2/FedRAMP alignment?

### Current Answers vs Gaps

| Customer Question | Current Answer | Gap? |
|---|---|---|
| Will it be maintained? | Yes — AWS-maintained, active dev | No formal commitment timeline |
| Security patch SLA? | AWS VDP + Dependabot daily | No published SLA |
| Breaking change policy? | Conventional commits + semver implied | No written deprecation policy |
| Multi-version support? | 1.x.x only, < 1.0 unsupported | No overlap support window |
| Enterprise support? | Not documented | Unclear if AWS Support covers it |
| SBOM / signed releases? | Not present | Gap |
| Security advisories? | Via AWS VDP | No GitHub Security Advisories |

---

## References

- [SECURITY.md](https://github.com/strands-agents/sdk-python/blob/main/SECURITY.md)
- [CONTRIBUTING.md](https://github.com/strands-agents/sdk-python/blob/main/CONTRIBUTING.md)
- [AWS Vulnerability Reporting](http://aws.amazon.com/security/vulnerability-reporting/)
- [HackerOne AWS VDP](https://hackerone.com/aws_vdp)
