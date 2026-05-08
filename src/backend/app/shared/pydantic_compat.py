from typing import Any, Dict, cast

from pydantic import BaseModel


def model_dump(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return cast(Dict[str, Any], model.model_dump())
    return cast(Dict[str, Any], model.dict())
