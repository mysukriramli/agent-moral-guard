# Agent Moral Guard 🛡️

[![Moral Guard Verification](https://github.com/mysukriramli/agent-moral-guard/actions/workflows/test.yml/badge.svg)](https://github.com/mysukriramli/agent-moral-guard/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

An autonomous, deterministic moral gating and citation engine for AI agents. 

Rather than relying on non-deterministic LLM system prompts, **Agent Moral Guard** intercepts proposed agent tool calls, queries a distilled Parquet knowledge base of 2,500+ codified ethical axioms via **DuckDB**, and emits deterministic verdicts attached to peer-reviewed academic and international legal citations.

---

## Datasets & Citation Attribution

Every rule evaluation attaches complete provenance data:

1. **ETHICS Benchmark (ICLR 2021)**: Hendrycks et al. — Deontology, Justice, Utilitarianism, and Virtue.
2. **Moral Stories (EMNLP 2021)**: Emelin et al. — Situated reasoning about norms, intent, and consequences.
3. **Social Chemistry 101 (EMNLP 2020)**: Forbes et al. — Everyday moral rules-of-thumb and social judgments.
4. **Universal Declaration of Human Rights (UN 1948)**: International legal invariants.

---

## Installation

```bash
git clone [https://github.com/mysukriramli/agent-moral-guard.git](https://github.com/mysukriramli/agent-moral-guard.git)
cd agent-moral-guard
pip install .
