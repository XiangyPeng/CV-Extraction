# Prompt Engineering

## Overview

This project uses OpenAI's `gpt-4o-mini` model to extract resume data. The API is configured via `.env` file.

## Goal

To improve the stability of LLM output, this project uses a dedicated prompt that instructs the model to return only structured JSON and avoid any explanatory text.

## Core Prompt Design

- Explicitly constrain the output format: `ONLY JSON`, `exact keys`, `valid JSON without markdown`
- Specify field names and types
- Provide document context (the raw resume text)

### Example Prompt

```text
Extract resume data and return ONLY JSON with the exact keys: name, email, phone, skills, education, experience. Response must be valid JSON without markdown or explanatory text.

Resume content:
<PDF extracted text>
```

## Variants and Result Comparison

You can try these prompt variants:

1. Require list format: `skills must be a list of strings`
2. Add validation rules: `email must be a valid email address`
3. Request normalized fields: `split skills by comma or newline`

Compare the output of each variant with `src/evaluation.py` to measure field accuracy.

## Why This Works

- Structured output reduces post-processing errors
- Specifying field names avoids inconsistent keys
- Banning markdown fences prevents parsing failures

## Evaluating Prompt Stability

Submit the same resume multiple times and track whether fields are extracted correctly. If the LLM fails, the system will trigger rule-based fallback parsing.

## Configuration

Set the following environment variables in `.env` file:

```env
OPENAI_API_KEY=sk-proj-xxx...          # Your OpenAI API key
OPENAI_MODEL=gpt-4o-mini              # Model to use
OPENAI_BASE_URL=https://api.openai.com/v1  # API endpoint
```

To obtain an API key:
1. Visit [OpenAI Platform](https://platform.openai.com)
2. Create an account or sign in
3. Go to **API Keys** section
4. Create a new secret key
5. Copy and paste into `.env` file
