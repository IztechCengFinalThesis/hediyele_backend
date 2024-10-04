from typing import Dict, Any

from tests.factories.base import FactoryBaseModel
from db.models.simple import SimpleModel


class SimpleFactory(FactoryBaseModel):
    """Simple factory."""

    _model = SimpleModel
    _uow_rep_name = "simple_table"

    def _init_all_field(self, kwargs: Dict[str, Any]) -> None:
        """
        Init all field to model.

        :param kwargs: Params to create model
        """
        if "name" not in kwargs:
            kwargs["name"] = self.faker.pystr(min_chars=4, max_chars=12)
