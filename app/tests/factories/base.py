import abc
import uuid
from datetime import datetime
from typing import Any, Optional, Dict

import pytz
from faker import Faker

from db.uow import UnitOfWork
from tests.utils import get_faker


class FactoryBaseModel(abc.ABC):
    """Factory base model."""

    _model: Any
    _uow_rep_name: str
    model_object: Any = None
    faker: Faker = get_faker()

    async def create(self, db_uow: Optional[UnitOfWork] = None, **kwargs: Any) -> Any:
        """
        Create model.

        :param db_uow: UOW object, if None - no create in db
        :param kwargs: Params to create model
        :return: instance model
        """
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "created_at" not in kwargs:
            kwargs["created_at"] = datetime.now(tz=pytz.utc)
        if "updated_at" not in kwargs:
            kwargs["updated_at"] = datetime.now(tz=pytz.utc)

        self._init_all_field(kwargs)

        model_instance = self._model(**kwargs)
        if db_uow is None:
            return model_instance

        async with db_uow:
            await getattr(db_uow, self._uow_rep_name).add_one(model_instance)
            return await getattr(db_uow, self._uow_rep_name).get_one(
                id=model_instance.id
            )

    @abc.abstractmethod
    def _init_all_field(self, kwargs: Dict[str, Any]) -> None:
        """
        Init all field to model.

        :param kwargs: Params to create model
        """
        raise NotImplementedError
