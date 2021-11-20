import functools
from typing import List, Dict, Optional, Union, Any, TypeVar, Type

from motor.motor_asyncio import AsyncIOMotorDatabase  # type: ignore
from pymongo.results import DeleteResult  # type: ignore

T = TypeVar("T")


def return_converted(func):
    @functools.wraps(func)
    async def wrapped(*args, **kwargs):
        data: Union[Dict, List[Dict]] = await func(*args, **kwargs)

        self: Document = args[0]
        if not self.converter:
            return data

        if not isinstance(data, list):
            return self.converter(**data)

        new_data = []
        for d in data:
            new_data.append(self.converter(**d))

        return new_data

    return wrapped


class Document:
    _version = 7

    def __init__(
        self, database: AsyncIOMotorDatabase, document_name: str, converter=None
    ):
        self._document_name: str = document_name
        self._database: AsyncIOMotorDatabase = database
        self.document = database[document_name]

        self.converter: Type[T] = converter

    # <-- Pointer Methods -->
    async def find(self, data_id: Any) -> Union[Dict[str, Any], Type[T]]:
        return await self.find_by_id(data_id)

    async def delete(self, data_id: Any) -> Optional[DeleteResult]:
        return await self.delete_by_id(data_id)

    async def update(self, data: Dict[str, Any], *args: Any, **kwargs: Any) -> None:
        await self.update_by_id(data, *args, **kwargs)

    # <-- Actual Methods -->
    @return_converted
    async def get_all(
        self, filter_dict: Optional[Dict[str, Any]] = None, *args: Any, **kwargs: Any
    ) -> List[Optional[Union[Dict[str, Any], Type[T]]]]:
        filter_dict = filter_dict or {}

        return await self.document.find(filter_dict, *args, **kwargs).to_list(None)  # type: ignore

    @return_converted
    async def find_by_id(self, data_id: Any) -> Union[Dict[str, Any], Type[T]]:
        return await self.document.find_one({"_id": data_id})  # type: ignore

    @return_converted
    async def find_by_custom(
        self, filter_dict: Dict[str, Any]
    ) -> Optional[Union[Dict[str, Any], Type[T]]]:
        self.__ensure_dict(filter_dict)

        return await self.document.find_one(filter_dict)  # type: ignore

    @return_converted
    async def find_many_by_custom(
        self, filter_dict: Dict[str, Any]
    ) -> List[Union[Dict[str, Any], Type[T]]]:
        self.__ensure_dict(filter_dict)

        return await self.document.find(filter_dict).to_list(None)  # type: ignore

    async def delete_by_id(self, data_id: Any) -> Optional[DeleteResult]:
        if await self.find_by_id(data_id) is None:
            return None

        return await self.document.delete_many({"_id": data_id})

    async def delete_by_custom(
        self, filter_dict: Dict[str, Any]
    ) -> Optional[Union[List[DeleteResult], DeleteResult]]:
        self.__ensure_dict(filter_dict)

        if await self.find_by_custom(filter_dict) is None:
            return None

        return await self.document.delete_many(filter_dict)  # type: ignore

    async def insert(self, data: Dict[str, Any]) -> None:
        self.__ensure_dict(data)

        await self.document.insert_one(data)

    async def upsert(
        self, data: Dict[str, Any], option: str = "set", *args: Any, **kwargs: Any
    ) -> None:
        await self.update_by_id(data, option, upsert=True, *args, **kwargs)

    async def update_by_id(
        self, data: Dict[str, Any], option: str = "set", *args: Any, **kwargs: Any
    ) -> None:
        self.__ensure_dict(data)
        self.__ensure_id(data)

        if await self.find_by_id(data["_id"]) is None:
            return await self.insert(data)

        data_id = data.pop("_id")
        await self.document.update_one(
            {"_id": data_id}, {f"${option}": data}, *args, **kwargs
        )

    async def upsert_custom(
        self,
        filter_dict: Dict[str, Any],
        update_data: Dict[str, Any],
        option: str = "set",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        await self.update_by_custom(
            filter_dict, update_data, option, upsert=True, *args, **kwargs
        )

    async def update_by_custom(
        self,
        filter_dict: Dict[str, Any],
        update_data: Dict[str, Any],
        option: str = "set",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.__ensure_dict(filter_dict)
        self.__ensure_dict(update_data)

        if not bool(await self.find_by_custom(filter_dict)):
            # Insert
            return await self.insert({**filter_dict, **update_data})

        # Update
        await self.document.update_one(
            filter_dict, {f"${option}": update_data}, *args, **kwargs
        )

    async def unset(self, data: Dict[str, Any]) -> None:
        self.__ensure_dict(data)
        self.__ensure_id(data)

        if await self.find_by_id(data["_id"]) is None:
            return

        data_id = data.pop("_id")
        await self.document.update_one({"_id": data_id}, {"$unset": data})

    async def increment(
        self, data_id: Any, amount: Union[int, float], field: str
    ) -> None:
        if await self.find_by_id(data_id) is None:
            return

        await self.document.update_one({"_id": data_id}, {"$inc": {field: amount}})

    # <-- Private methods -->
    @staticmethod
    def __ensure_dict(data: Dict[str, Any]) -> None:
        assert isinstance(data, dict)

    @staticmethod
    def __ensure_id(data: Dict[str, Any]) -> None:
        assert "_id" in data

    @property
    def document_name(self) -> str:
        return self._document_name

    @property
    def database(self) -> AsyncIOMotorDatabase:
        return self._database
