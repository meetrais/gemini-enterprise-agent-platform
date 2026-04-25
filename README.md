# Gemini Enterprise Agent Platform — Implementation Guide

This is a hands-on, step-by-step implementation guide for building, deploying, governing, and distributing enterprise agents with **Gemini Enterprise**, **Vertex AI Agent Engine**, and the **Agent Development Kit (ADK)**.

You will build one realistic system end-to-end: an **Enterprise Support Assistant** that triages customer questions, retrieves answers from internal docs, executes account actions through tools, remembers users across sessions, and can be registered for use in the Gemini Enterprise web app.

## How to use this guide

Follow the sections in order. Each file is self-contained and ends with a "What you should have now" checklist — finish it before moving to the next.

| # | File | Pillar | What you build |
|---|------|--------|----------------|
| 00 | `00_prerequisites.md` | Foundation | Accounts, IAM roles, software you need installed |
| 01 | `01_project_setup.md` | Foundation | GCP project, APIs, staging bucket, SDKs |
| 02 | `02_model_garden.md` | Build | Choose a model, tune it, evaluate it |
| 03 | `03_agent_studio.md` | Build | Low-code triage agent in Agent Designer |
| 04 | `04_adk_basics.md` | Build | First code-first agent with ADK |
| 05 | `05_tools.md` | Build | Function tools, OpenAPI, MCP, Code Execution |
| 06 | `06_rag_grounding.md` | Build | RAG Engine and Vector Search for private data |
| 07 | `07_memory_bank.md` | Build | Agent Engine Sessions and Memory Bank |
| 08 | `08_multi_agent.md` | Build | Multi-agent orchestration and A2A concepts |
| 09 | `09_deployment.md` | Scale | Deploy to Vertex AI Agent Engine, Cloud Run, or GKE |
| 10 | `10_governance.md` | Govern | IAM, Gemini Enterprise registration, Model Armor |
| 11 | `11_optimization.md` | Optimize | Simulation, Evaluation, Observability |
| 12 | `12_distribution.md` | Distribute | Surface in the Gemini Enterprise web app |
| 13 | `13_checklist_and_cleanup.md` | — | Final E2E checklist and resource cleanup |

## Conventions used throughout

- Lines starting with `PS>` mean Windows PowerShell. Lines starting with `$` mean macOS/Linux Bash or Zsh. Plain code blocks are file contents (Python, YAML, JSON).
- Wherever you see `<ANGLE_BRACKETS>` in commands, replace with your own value.
- Most `gcloud` commands are the same on Windows, macOS, and Linux. The differences are usually environment variables, virtual environment activation, path separators, and line-continuation characters.
- The running example uses these names — change them only if you have a reason to:
  - **Project ID:** `my-agent-platform`
  - **Region:** `us-central1`
  - **Staging bucket:** `gs://my-agent-platform-agent-staging`
  - **Service account:** `agent-runner@my-agent-platform.iam.gserviceaccount.com`

## A note on dates and previews

This guide was reviewed against public Google Cloud documentation in April 2026. Several agent features are still marked Preview in the docs, so exact API names, console labels, and command surfaces can shift. If a command fails, check the linked Google Cloud docs before assuming you typed it wrong.

## Primary references

- Gemini Enterprise: https://docs.cloud.google.com/gemini/enterprise/docs
- Gemini Enterprise agents: https://docs.cloud.google.com/gemini/enterprise/docs/agents-overview
- Vertex AI Agent Engine: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview
- ADK docs: https://google.github.io/adk-docs/
- Model Armor: https://docs.cloud.google.com/model-armor
- Gen AI Evaluation: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/evaluation-overview

Ready? Open `00_prerequisites.md` to start.
