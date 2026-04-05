# AI Workflow Automation Engine

A framework for building AI-powered business workflow automations. Chain LLM calls with tools, conditions, loops, and human-in-the-loop checkpoints — all defined in simple YAML.

## Features

- **YAML-based workflow definitions** — no code needed for simple automations
- **LLM-powered decision nodes** — AI evaluates conditions and routes data
- **Built-in integrations** — Email, HTTP APIs, databases, file I/O, Slack webhooks
- **Human-in-the-loop** — optional approval checkpoints for sensitive actions
- **Retry & error handling** — configurable backoff, dead-letter queues
- **Observability** — structured logging, run history, timing metrics

## Use Cases

- **Email triage**: Classify incoming emails, draft responses, auto-respond to routine queries
- **Lead processing**: Parse form submissions, score leads, update CRM, send notifications
- **Report generation**: Aggregate data from multiple sources, generate summaries, distribute
- **Document processing**: Extract structured data from PDFs/images, validate, store
- **Social media**: Monitor mentions, draft responses, schedule posts

## Tech Stack

Python 3.11+, PyYAML, LiteLLM, aiohttp, SQLAlchemy, pydantic

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env
# Define your workflow in workflows/
python runner.py --workflow workflows/email_triage.yaml
```

## Example Workflow

```yaml
name: email-triage
description: Classify and route incoming emails

triggers:
  - type: poll
    source: imap
    config:
      host: imap.gmail.com
      folder: INBOX
      interval: 60

nodes:
  - id: classify
    type: llm
    model: openai/gpt-4o-mini
    prompt: |
      Classify this email into one of: urgent, support, spam, newsletter
      Subject: {{email.subject}}
      Body: {{email.body[:500]}}
    output_key: category

  - id: route-urgent
    type: condition
    check: "{{classify.category}} == 'urgent'"
    then: notify-slack

  - id: route-support
    type: condition
    check: "{{classify.category}} == 'support'"
    then: draft-response

  - id: notify-slack
    type: webhook
    url: "{{secrets.slack_webhook}}"
    method: POST
    body:
      text: "🚨 Urgent email from {{email.from}}: {{email.subject}}"

  - id: draft-response
    type: llm
    model: openai/gpt-4o-mini
    prompt: |
      Draft a helpful response to this customer support email.
      Be professional but friendly. Sign off as the support team.
      Subject: {{email.subject}}
      Body: {{email.body}}
    human_review: true  # Require approval before sending

  - id: archive-spam
    type: condition
    check: "{{classify.category}} == 'spam' or {{classify.category}} == 'newsletter'"
    then: move-to-folder
```

## Project Structure

```
ai-workflow-automation/
├── runner.py            # CLI workflow runner
├── engine/
│   ├── workflow.py      # Workflow parser and executor
│   ├── nodes/
│   │   ├── llm.py       # LLM decision nodes
│   │   ├── condition.py # Conditional routing
│   │   ├── webhook.py   # HTTP webhook calls
│   │   ├── email.py     # Email send/receive
│   │   └── transform.py # Data transformation
│   ├── scheduler.py     # Trigger/poll management
│   └── state.py         # Run state and history
├── workflows/
│   └── email_triage.yaml
├── requirements.txt
├── .env.example
├── README.md
└── tests/
    └── test_engine.py
```

## License

MIT
