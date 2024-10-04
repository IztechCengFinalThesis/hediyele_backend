from typing import Annotated

from fastapi import Depends

from db.uow import UnitOfWork

UnitOfWorkDep = Annotated[UnitOfWork, Depends(UnitOfWork)]
