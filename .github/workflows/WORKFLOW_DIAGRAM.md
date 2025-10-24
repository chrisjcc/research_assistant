# CI/CD Workflow Architecture

## Visual Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         GitHub Repository                        │
└─────────────────────────────────────────────────────────────────┘
                                 │
                 ┌───────────────┼───────────────┐
                 │               │               │
                 ▼               ▼               ▼
         ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
         │   Push/PR    │ │   Schedule   │ │   Git Tag    │
         │   to main/   │ │  (Daily 2AM) │ │  (v*.*.*)    │
         │   develop    │ │              │ │              │
         └──────────────┘ └──────────────┘ └──────────────┘
                 │               │               │
                 ▼               ▼               ▼
         ┌──────────────────────────────────────────────┐
         │         Workflow Orchestration                │
         └──────────────────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  tests.yml      │    │  security.yml   │    │  release.yml    │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │    Lint     │ │    │ │  Dep Scan   │ │    │ │  Validate   │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │    Test     │ │    │ │Secret Scan  │ │    │ │    Build    │ │
│ │  (3.10-12)  │ │    │ └─────────────┘ │    │ └─────────────┘ │
│ └─────────────┘ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ ┌─────────────┐ │    │ │  Code Scan  │ │    │ │   Release   │ │
│ │ Type Check  │ │    │ └─────────────┘ │    │ └─────────────┘ │
│ └─────────────┘ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ ┌─────────────┐ │    │ │   CodeQL    │ │    │ │   Publish   │ │
│ │   Summary   │ │    │ └─────────────┘ │    │ │    PyPI     │ │
│ └─────────────┘ │    │ ┌─────────────┐ │    │ └─────────────┘ │
└─────────────────┘    │ │License Scan │ │    │ ┌─────────────┐ │
                       │ └─────────────┘ │    │ │   Docker    │ │
         ▲             │ ┌─────────────┐ │    │ │   Publish   │ │
         │             │ │Container Scn│ │    │ └─────────────┘ │
         │             │ └─────────────┘ │    └─────────────────┘
         │             └─────────────────┘              │
         │                                              │
         │             ┌─────────────────┐              │
         └─────────────│    pr.yml       │              │
                       │                 │              │
                       │ ┌─────────────┐ │              │
                       │ │ PR Validate │ │              │
                       │ └─────────────┘ │              │
                       │ ┌─────────────┐ │              │
                       │ │Size Label   │ │              │
                       │ └─────────────┘ │              │
                       │ ┌─────────────┐ │              │
                       │ │Dep Review   │ │              │
                       │ └─────────────┘ │              │
                       │ ┌─────────────┐ │              │
                       │ │  Coverage   │ │              │
                       │ └─────────────┘ │              │
                       │ ┌─────────────┐ │              │
                       │ │Auto-Label   │ │              │
                       │ └─────────────┘ │              │
                       └─────────────────┘              │
                                 │                      │
                                 ▼                      ▼
                       ┌─────────────────────────────────────┐
                       │         Outputs & Artifacts         │
                       ├─────────────────────────────────────┤
                       │ • Test Reports                      │
                       │ • Coverage Reports                  │
                       │ • Security Scan Results             │
                       │ • GitHub Releases                   │
                       │ • PyPI Packages                     │
                       │ • Docker Images                     │
                       │ • PR Comments & Labels              │
                       └─────────────────────────────────────┘
```

## Workflow Triggers

### Event-Based Triggers

```
┌─────────────────────────────────────────────────────────────┐
│                         Events                              │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
    ┌────────┐          ┌────────┐          ┌────────┐
    │  Push  │          │   PR   │          │  Tag   │
    └────────┘          └────────┘          └────────┘
         │                    │                    │
         ├────────────────────┼────────────────────┤
         │                    │                    │
    ┌────▼─────┐         ┌───▼────┐          ┌────▼─────┐
    │ tests.yml│         │pr.yml  │          │release.yml│
    │security.yml        └────────┘          └──────────┘
    └──────────┘
```

### Time-Based Triggers

```
┌──────────────────────────────────────────┐
│     Cron Schedule (Daily 2 AM UTC)       │
└──────────────────────────────────────────┘
                    │
                    ▼
         ┌──────────────────┐
         │   security.yml   │
         │                  │
         │  • Dep Scan      │
         │  • Secret Scan   │
         │  • Code Scan     │
         │  • CodeQL        │
         │  • License Scan  │
         │  • Container Scan│
         └──────────────────┘
```

## Job Dependencies

### Tests Workflow
```
     lint
       │
       ├────┐
       │    │
       ▼    ▼
     test  type-check
       │    │
       └────┼────┐
            │    │
            ▼    ▼
         test-summary
```

### Security Workflow
```
dependency-scan   secret-scan   code-scan   codeql-analysis   license-scan
       │              │             │              │               │
       └──────────────┼─────────────┼──────────────┼───────────────┘
                      │             │              │
                      ▼             ▼              ▼
                         security-summary
```

### Release Workflow
```
    validate
       │
       ▼
     build
       │
       ├──────────────┐
       │              │
       ▼              ▼
  create-release  upload-assets
       │              │
       └──────┬───────┘
              │
    ┌─────────┼─────────┐
    │         │         │
    ▼         ▼         ▼
publish-pypi docker  notify
```

### PR Workflow
```
pr-validation  dependency-review  code-coverage  auto-label
       │              │                 │            │
       └──────────────┼─────────────────┼────────────┘
                      │                 │
                      ▼                 ▼
                  pr-comment
```

## Data Flow

### Test Results Flow
```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  pytest  │────>│ Coverage │────>│ Codecov  │
└──────────┘     └──────────┘     └──────────┘
                      │
                      ▼
                ┌──────────┐
                │Artifacts │
                └──────────┘
```

### Security Scan Flow
```
┌─────────┐     ┌──────────┐     ┌──────────┐
│ Scanner │────>│  Report  │────>│ Security │
│ (6 tools)     │  (JSON)  │     │   Tab    │
└─────────┘     └──────────┘     └──────────┘
                      │
                      ▼
                ┌──────────┐
                │Artifacts │
                └──────────┘
```

### Release Flow
```
┌──────┐     ┌───────┐     ┌──────────┐     ┌─────────┐
│ Tag  │────>│ Build │────>│ Release  │────>│  PyPI   │
└──────┘     └───────┘     └──────────┘     └─────────┘
                                │
                                ├────────────>│ Docker  │
                                │             └─────────┘
                                ▼
                          ┌──────────┐
                          │  GitHub  │
                          │ Release  │
                          └──────────┘
```

## Integration Points

### External Services
```
┌──────────────────────────────────────────────────────────┐
│                    GitHub Actions                         │
└──────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
   │ Codecov │    │  PyPI   │    │  Docker │    │  GitHub │
   └─────────┘    └─────────┘    │   Hub   │    │ Security│
                                  └─────────┘    │   Tab   │
                                                 └─────────┘
```

### Notification Flow
```
┌──────────────────────────────────────────────────────────┐
│                    Workflow Events                        │
└──────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
         ┌────────┐    ┌────────┐    ┌────────┐
         │ Email  │    │ Slack  │    │Discord │
         └────────┘    └────────┘    └────────┘
```

## Caching Strategy

```
┌─────────────────────────────────────────────────────────┐
│                     Cache Layers                         │
├─────────────────────────────────────────────────────────┤
│  Layer 1: pip packages (~/.cache/pip)                   │
│  Layer 2: mypy cache (.mypy_cache)                      │
│  Layer 3: pytest cache (.pytest_cache)                  │
│  Layer 4: Docker layers (buildx cache)                  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
                   Faster Builds (40-60% time saved)
```

## Artifact Lifecycle

```
Create Artifact          Upload              Retention            Delete
      │                    │                    │                   │
      ▼                    ▼                    ▼                   ▼
┌──────────┐        ┌──────────┐        ┌──────────┐        ┌──────────┐
│Generated │───────>│  GitHub  │───────>│ 7-30 days│───────>│Automatic │
│  Files   │        │ Storage  │        │  stored  │        │ cleanup  │
└──────────┘        └──────────┘        └──────────┘        └──────────┘
```

## Security Scanning Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     Security Layers                          │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: Secrets in Git History (TruffleHog)                │
│ Layer 2: Vulnerable Dependencies (Safety, pip-audit)        │
│ Layer 3: Code Vulnerabilities (Bandit, Semgrep)             │
│ Layer 4: Semantic Analysis (CodeQL)                         │
│ Layer 5: License Compliance (pip-licenses)                  │
│ Layer 6: Container Vulnerabilities (Trivy)                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
              Comprehensive Security Coverage
```

## Release Pipeline Stages

```
Validate ──> Build ──> Create Release ──> Publish ──> Notify
   │           │              │              │          │
   ▼           ▼              ▼              ▼          ▼
  Tests    Package      GitHub Pages     PyPI       Success
            Wheel          + Assets      Docker    Webhooks
```

## Coverage Reporting Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     Coverage Pipeline                        │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
    ┌────────┐          ┌────────┐          ┌────────┐
    │Unit Test          │Integr. │          │ Total  │
    │Coverage│          │ Test   │          │Coverage│
    └────────┘          │Coverage│          └────────┘
         │              └────────┘               │
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                   ┌─────────┼─────────┐
                   │         │         │
                   ▼         ▼         ▼
              ┌────────┐ ┌──────┐ ┌───────┐
              │Codecov │ │ HTML │ │  PR   │
              │Dashboard   │Report│ │Comment│
              └────────┘ └──────┘ └───────┘
```

## Legend

```
┌─────────────────────────────────────────────────────────────┐
│                         Symbols                              │
├─────────────────────────────────────────────────────────────┤
│  ┌──────┐                                                    │
│  │ Box  │  = Workflow, Job, or Process                      │
│  └──────┘                                                    │
│                                                              │
│     │                                                        │
│     ▼     = Data or Control Flow                            │
│                                                              │
│     ├──   = Branch/Split in Flow                            │
│                                                              │
│     └──   = Merge/Join in Flow                              │
└─────────────────────────────────────────────────────────────┘
```

## Quick Reference

| Workflow | Primary Purpose | Trigger | Duration |
|----------|----------------|---------|----------|
| tests.yml | Quality checks | Push/PR | 5-10min |
| security.yml | Vulnerability scan | Push/PR/Schedule | 5-15min |
| release.yml | Package publish | Tag | 10-20min |
| pr.yml | PR automation | PR events | 2-5min |

---

**Note**: This diagram represents the logical flow and relationships between workflows. Actual execution may vary based on conditions, failures, or manual interventions.
