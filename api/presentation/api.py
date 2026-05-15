from contextlib import asynccontextmanager
from typing import Any
from fastapi import Depends, FastAPI

from api.infra.config import get_settings
from api.infra.database import init_database
from api.infra.factories import create_transaction_exporter, create_transaction_queue
from api.infra.locks import InMemoryAccountLockProvider
from api.infra.
from api.presentation.routes