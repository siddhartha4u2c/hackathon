# PartsPilot Copilot

PartsPilot is a small, self-contained after-sales Copilot prototype. It imports the supplied workbook into PostgreSQL, investigates purchase orders and claims across joined records, and optionally uses an OpenAI-compatible LLMAAS endpoint to phrase grounded answers.

## Run on EC2 with Docker Compose

1. Copy this folder and the sample workbook to the EC2 instance.
2. Install Docker and Docker Compose on the instance.
3. Create the environment file:

   ```sh
   cp .env.example .env
   ```

4. Set `POSTGRES_PASSWORD`, `LLMAAS_BASE_URL`, `LLMAAS_API_KEY`, and `LLMAAS_MODEL` in `.env`.
   `LLMAAS_BASE_URL` should be the provider's OpenAI-compatible API base URL; the application appends `/chat/completions`.
5. Start the stack:

   ```sh
   docker compose up -d --build
   ```

6. Open `http://<ec2-public-ip>:8000`.

The PostgreSQL data is stored in the named `postgres_data` Docker volume. For the prototype, back up that volume or run regular `pg_dump` exports. Do not expose port 5432 in the EC2 security group.

## Local questions to try

- `Investigate claim CLM-4021`
- `What is the status of PO-2026-1042?`

The application still returns deterministic evidence when LLMAAS is not configured. When the key and endpoint are configured, the evidence is passed to the LLM and the response is generated with instructions not to invent transactional facts.

## Security

The LLMAAS key is used only by the backend container. It must not be placed in the frontend, Dockerfile, workbook, or source code. For a longer-lived deployment, inject it with AWS Systems Manager Parameter Store or Secrets Manager.
