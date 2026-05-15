from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from src.database.session import get_session

DbSession = Annotated[Session, Depends(get_session)]
