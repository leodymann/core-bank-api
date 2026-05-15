import asyncio
from pathlib import Path

from api.domain.entities import Transaction


class NoopTransactionExporter:
    async def export(self, transaction: Transaction) -> None:
        return None


class MarkdownTransactionExporter:
    def __init__(self, directory: str) -> None:
        self._directory = Path(directory)

    async def export(self, transaction: Transaction) -> None:
        await asyncio.to_thread(self._write_file, transaction)

    def _write_file(self, transaction: Transaction) -> None:
        self._directory.mkdir(parents=True, exist_ok=True)
        path = self._directory / f"{transaction.id}.md"
        status = transaction.status.value
        failure_reason = transaction.failure_reason or ""
        content = f"""---
type: transaction
transaction_id: "{transaction.id}"
status: "{status}"
amount: "{transaction.amount}"
source_account_id: "{transaction.source_account_id}"
destination_account_id: "{transaction.destination_account_id}"
idempotency_key: "{transaction.idempotency_key}"
created_at: "{transaction.created_at.isoformat()}"
updated_at: "{transaction.updated_at.isoformat()}"
failure_reason: "{failure_reason}"
tags:
  - banking
  - transaction
  - transaction/{status}
---

# Transaction {transaction.id}

Status: **{status}**

Amount: **{transaction.amount}**

Source account: [[account-{transaction.source_account_id}]]

Destination account: [[account-{transaction.destination_account_id}]]

Idempotency key: `{transaction.idempotency_key}`

Created at: `{transaction.created_at.isoformat()}`

Updated at: `{transaction.updated_at.isoformat()}`

Failure reason: {failure_reason or "none"}
"""
        path.write_text(content, encoding="utf-8")

