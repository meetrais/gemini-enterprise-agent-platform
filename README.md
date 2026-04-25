# Gemini Enterprise Agent Platform - Implementation Guide

This is a hands-on, step-by-step implementation guide for building, deploying, governing, and distributing enterprise agents with **Gemini Enterprise**, **Agent Runtime (Agent Engine)**, and the **Agent Development Kit (ADK)**.

You will build one realistic system end-to-end: an **Enterprise Support Assistant** that triages customer questions, retrieves answers from internal docs, executes account actions through tools, remembers users across sessions, and can be registered for use in the Gemini Enterprise web app.

## How to use this guide

Follow the sections in order. Each file is self-contained and ends with a "What you should have now" checklist - finish it before moving to the next.

| # | File | Pillar | What you build |
|---|------|--------|----------------|
| 01 | [`01_prerequisites.md`](01_prerequisites.md) | Foundation | Accounts, IAM roles, software you need installed |
| 02 | [`02_project_setup.md`](02_project_setup.md) | Foundation | GCP project, APIs, staging bucket, SDKs |
| 03 | [`03_model_garden.md`](03_model_garden.md) | Build | Choose a model, tune it, evaluate it |
| 04 | [`04_agent_studio.md`](04_agent_studio.md) | Build | Low-code triage agent in Agent Designer |
| 05 | [`05_adk_basics.md`](05_adk_basics.md) | Build | First code-first agent with ADK |
| 06 | [`06_tools.md`](06_tools.md) | Build | Function tools, OpenAPI, MCP, Code Execution |
| 07 | [`07_rag_grounding.md`](07_rag_grounding.md) | Build | RAG Engine and Vector Search for private data |
| 08 | [`08_memory_bank.md`](08_memory_bank.md) | Build | Agent Engine Sessions and Memory Bank |
| 09 | [`09_multi_agent.md`](09_multi_agent.md) | Build | Multi-agent orchestration and A2A concepts |
| 10 | [`10_deployment.md`](10_deployment.md) | Scale | Deploy to Agent Runtime (Agent Engine), Cloud Run, or GKE |
| 11 | [`11_governance.md`](11_governance.md) | Govern | IAM, Gemini Enterprise registration, Model Armor |
| 12 | [`12_optimization.md`](12_optimization.md) | Optimize | Simulation, Evaluation, Observability |
| 13 | [`13_distribution.md`](13_distribution.md) | Distribute | Surface in the Gemini Enterprise web app |
| 14 | [`14_checklist_and_cleanup.md`](14_checklist_and_cleanup.md) | - | Final E2E checklist and resource cleanup |

## Conventions used throughout

- Lines starting with `PS>` mean Windows PowerShell. Lines starting with `$` mean macOS/Linux Bash or Zsh. Plain code blocks are file contents (Python, YAML, JSON).
- Wherever you see `<ANGLE_BRACKETS>` in commands, replace with your own value.
- Most `gcloud` commands are the same on Windows, macOS, and Linux. The differences are usually environment variables, virtual environment activation, path separators, and line-continuation characters.
- The running example uses these names - change them only if you have a reason to:
 - **Project ID:** `my-agent-platform`
 - **Region:** `us-central1`
 - **Staging bucket:** `gs://my-agent-platform-agent-staging`
 - **Service account:** `agent-runner@my-agent-platform.iam.gserviceaccount.com`

## A note on dates and previews

This guide was reviewed against public Google Cloud documentation in April 2026. Several agent features are still marked Preview in the docs, so exact API names, console labels, and command surfaces can shift. If a command fails, check the linked Google Cloud docs before assuming you typed it wrong.

## Primary references

- Gemini Enterprise: https://docs.cloud.google.com/gemini/enterprise/docs
- Gemini Enterprise agents: https://docs.cloud.google.com/gemini/enterprise/docs/agents-overview
- Agent Runtime (Agent Engine): https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview
- ADK docs: https://google.github.io/adk-docs/
- Model Armor: https://docs.cloud.google.com/model-armor
- Gen AI Evaluation: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/evaluation-overview

Ready? Open `01_prerequisites.md` to start.
