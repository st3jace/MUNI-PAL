# CLAUDE.md — Model Selection Optimization Directive

## Purpose

This directive governs intelligent model selection throughout all coding sessions in this workspace. The objective is to optimize cost-efficiency and output quality by matching model capability to task complexity, using a hybrid of structured task classification and observable session indicators.

---

## Model Hierarchy & Roles

| Model | Alias | Role | Use When |
|-------|-------|------|----------|
| **Opus 4.6** | `opus` | Strategic Architect | Complex reasoning, multi-system design, novel problem-solving, debugging elusive issues |
| **Sonnet 4.5** | `sonnet` | Primary Workhorse | Standard development, implementation, refactoring, most coding tasks |
| **Haiku 4.5** | `haiku` | Rapid Executor | Formatting, simple edits, boilerplate generation, file manipulation, repetitive transforms |

**Default starting model: `sonnet`**
Only escalate to `opus` or descend to `haiku` when task classification warrants it.

---

## Task Classification Framework

Before beginning any task, classify it using the following rubric. When a task spans multiple tiers, use the highest applicable tier for the planning phase, then descend for execution.

### Tier 1 — Opus (Complex / High-Stakes)

Invoke Opus (`/model opus` or use `opusplan`) when the task meets **two or more** of these criteria:

- **Architectural decisions**: Designing system structure, choosing between competing patterns, establishing interfaces across multiple modules
- **Novel problem-solving**: No clear precedent or template exists; requires original reasoning about approach
- **Multi-file coordination**: Changes must be logically consistent across 4+ interdependent files
- **Debugging complex failures**: Root cause is non-obvious after initial investigation; involves race conditions, state management issues, or cross-system interactions
- **Security-sensitive logic**: Authentication flows, encryption implementation, access control, financial calculations
- **Specification interpretation**: Translating ambiguous business requirements into technical design (e.g., EMMA crawler session management architecture, Standard Model analytical pipeline design)
- **Performance optimization**: Algorithmic complexity analysis, identifying bottlenecks in data pipelines

**Effort level guidance for Opus:**
- `high` — Architectural design, security review, novel algorithms
- `medium` — Complex debugging, multi-file refactoring
- `low` — Quick architectural questions, design validation

### Tier 2 — Sonnet (Standard Development)

Sonnet is the default. Use it for everything that doesn't clearly belong in Tier 1 or Tier 3:

- Implementing a defined design or specification
- Writing functions, classes, and modules from clear requirements
- Standard debugging (error messages point to likely cause)
- Writing tests for existing code
- Refactoring within a single module or 2-3 related files
- API integration with documented endpoints
- Code review and quality improvements
- Documentation writing with technical depth

### Tier 3 — Haiku (Routine / Mechanical)

Descend to Haiku (`/model haiku`) when the task is primarily mechanical:

- Adding comments or docstrings to existing code
- Renaming variables, functions, or files across a codebase
- Generating boilerplate (config files, type definitions, repetitive CRUD operations)
- Simple find-and-replace patterns
- Formatting or linting fixes
- Converting between data formats (JSON ↔ CSV ↔ YAML) with no logic changes
- Generating test data or fixtures
- File organization and cleanup tasks

---

## Session Management Protocol

### When to Use `opusplan` vs. Manual Switching

**Use `opusplan`** when:
- A task has a clear plan-then-execute structure
- You want Opus reasoning for architecture but Sonnet efficiency for implementation
- The session will involve a single cohesive task with both design and coding phases

**Use manual `/model` switching** when:
- You're working through multiple unrelated tasks in one session
- You need Haiku for a batch of mechanical sub-tasks before returning to Sonnet
- The task boundaries don't align with plan/execute phases

### Context Window Cost Management

Switching models mid-session forces the new model to process the entire conversation history. To minimize waste:

1. **Break long sessions by tier**: If you accumulate 15+ exchanges at Sonnet level and need to escalate to Opus for a new sub-task, consider starting a fresh session with Opus rather than switching mid-conversation
2. **Batch Haiku tasks**: Collect mechanical tasks and execute them in a dedicated Haiku session rather than switching back and forth
3. **Front-load Opus work**: When a project involves both architectural decisions and implementation, start the session at Opus for design, then switch to Sonnet for implementation (natural `opusplan` flow)

---

## Observable Escalation Indicators

When working at Sonnet tier, escalate to Opus if you observe any of the following during the session:

| Indicator | What It Looks Like | Action |
|-----------|-------------------|--------|
| **Repeated failed attempts** | 3+ attempts to solve the same problem with different approaches, none resolving the root cause | Escalate to Opus |
| **Cascading side effects** | A fix in one file breaks behavior in another, suggesting a design-level issue | Escalate to Opus |
| **Ambiguous requirements** | The task cannot proceed without making assumptions that could invalidate significant work | Escalate to Opus for requirement analysis |
| **Cross-domain reasoning** | The solution requires understanding interactions between networking, database, UI, and business logic simultaneously | Escalate to Opus |
| **Performance/algorithmic complexity** | Naive implementation works but doesn't meet performance requirements; optimization requires algorithmic analysis | Escalate to Opus |

When working at Sonnet tier, descend to Haiku if you observe:

| Indicator | What It Looks Like | Action |
|-----------|-------------------|--------|
| **Repetitive pattern** | Applying the same transform to 5+ similar files/functions | Descend to Haiku |
| **Template-driven output** | Generating code that follows an established pattern with only variable substitution | Descend to Haiku |
| **Zero decision-making** | Task requires no judgment calls — purely mechanical execution | Descend to Haiku |

---

## Project-Specific Context: Launch Shop Operations

The following task categories are common in this workspace. Use these pre-classifications to reduce classification overhead:

### MPA Agent Development
- **Opus**: Designing agent decision trees, workflow state machines, error recovery architecture
- **Sonnet**: Implementing individual workflow handlers, API integrations with Google Workspace, writing agent response templates
- **Haiku**: Updating configuration files, adding new field mappings, generating test fixtures for bond application data

### EMMA Web Crawler
- **Opus**: Session management architecture (ViewState handling, collect-first strategy), anti-detection patterns, incremental data collection protocol design
- **Sonnet**: Implementing Playwright page interactions, parsing HTML tables, building data storage schemas, error handling for individual scraping steps
- **Haiku**: Generating URL lists, formatting extracted data, creating CSV/JSON output templates

### Standard Model Analytics
- **Opus**: Designing the SΩ calculation pipeline, implementing Omega ratio computations, building the comparative index framework, interpreting edge cases in the mathematical formulas
- **Sonnet**: Implementing individual calculation functions (geometric mean, MDDD, annualized risk), data ingestion from Yahoo Finance/Zacks, building visualization components
- **Haiku**: Data format conversions, generating report templates, updating sector classification mappings

### Bond Operations Dashboards
- **Opus**: Dashboard architecture decisions, data flow design between tracking systems
- **Sonnet**: Building dashboard components, implementing lead tracking logic, fee calculation modules
- **Haiku**: Updating static content, adding new fields to existing forms, CSS/styling adjustments

---

## Cost Optimization Summary

| Strategy | Estimated Savings | Implementation |
|----------|------------------|----------------|
| Default to Sonnet instead of Opus | ~80% per token | Set `ANTHROPIC_MODEL=sonnet` as environment default |
| Use `opusplan` for mixed tasks | ~40-60% vs. pure Opus | `/model opusplan` at session start |
| Batch mechanical work to Haiku | ~95% vs. Opus for those tasks | Dedicated Haiku sessions for bulk operations |
| Start new sessions instead of mid-session switching | Avoids reprocessing full history | Break at natural task boundaries |
| Use Opus effort levels | Variable savings on Opus usage | Low effort for quick checks, high for deep reasoning |

---

## Quick Reference Card

```
SESSION START CHECKLIST:
1. What am I building? → Classify the primary task tier
2. Does it have plan + execute phases? → Use opusplan
3. Is it purely mechanical? → Start at Haiku
4. Default → Start at Sonnet

MID-SESSION CHECKS:
- Am I stuck after 3 attempts? → /model opus
- Am I repeating the same pattern? → /model haiku
- Did I just finish the hard part? → /model sonnet

SESSION HYGIENE:
- Long conversation + need to switch up? → New session
- Multiple unrelated tasks? → Separate sessions per tier
- Done with Opus reasoning? → Switch to sonnet for implementation
```

---

## Environment Configuration

Add to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
# Default to Sonnet for cost efficiency
export ANTHROPIC_MODEL="claude-sonnet-4-5-20250929"

# Set effort level for when Opus is used
export CLAUDE_CODE_EFFORT_LEVEL="medium"

# Enable prompt caching (default, but explicit for clarity)
# Caching reduces costs by reusing repeated prompt prefixes
```

To override per-session:
```bash
# Architecture session
claude --model opus

# Bulk operations session
claude --model haiku

# Standard development (default)
claude
```
