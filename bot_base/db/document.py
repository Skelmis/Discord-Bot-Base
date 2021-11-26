import functools
from typing import List, Dict, Optional, Union, Any, TypeVar, Type

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.results import DeleteResult

T = TypeVar("T")


def return_converted(func):
    """
    If we have a registered converter,
    this deco will attempt to parse
    the given data into our provided
    class through the use of dictionary unpacking.
    """

    @functools.wraps(func)
    async def wrapped(*args, **kwargs):
        data: Union[Dict, List[Dict]] = await func(*args, **kwargs)

        self: Document = args[0]
        if not data or not self.converter:
            return data

        if not isinstance(data, list):
            return self.converter(**data)

        new_data = []
        for d in data:
            new_data.append(self.converter(**d))

        return new_data

    return wrapped


class Document:
    _version = 8

    def __init__(
        self,
        database: AsyncIOMotorDatabase,
        document_name: str,
        converter: Optional[Type[T]] = None,
    ):
        """
        Parameters
        ----------
        database: AsyncIOMotorDatabase
            The database we are connected to
        document_name: str
            What this document should be called
        converter: Optional[Type[T]]
            An optional converter to try
            convert all data-types which
            return either Dict or List into
        """
        self._document_name: str = document_name
        self._database: AsyncIOMotorDatabase = database
        self.document = database[document_name]

        self.converter: Type[T] = converter

    # <-- Pointer Methods -->
    async def find(self, data_id: Any) -> Optional[Union[Dict[str, Any], Type[T]]]:
        """
        Find and return one item.

        Parameters
        ----------
        data_id: Any
            The _id of the item to find

        Returns
        -------
        Optional[Union[Dict[str, Any], Type[T]]]
            The result of the query
        """
        return await self.find_by_id(data_id)

    async def delete(self, data_id: Any) -> Optional[DeleteResult]:
        """
        Delete an item from the Document
        if an item with that _id exists

        Parameters
        ----------
        data_id: Any
            The _id to delete

        Returns
        -------
        Optional[DeleteResult]
            The result of deletion
        """
        return await self.delete_by_id(data_id)

    async def update(self, data: Dict[str, Any], *args: Any, **kwargs: Any) -> None:
        """
        Update an existing document by _id

        Parameters
        ----------
        data: Dict[str, Any]
            The data we want to update with
        """
        await self.update_by_id(data, *args, **kwargs)

    # <-- Actual Methods -->
    @return_converted
    async def get_all(
        self, filter_dict: Optional[Dict[str, Any]] = None, *args: Any, **kwargs: Any
    ) -> List[Optional[Union[Dict[str, Any], Type[T]]]]:
        """
        Fetches and returns all items
        which match the given filter.

        Parameters
        ----------
        filter_dict: Optional[Dict[str, Any]]
            What to filter based on

        Returns
        -------
        List[Optional[Union[Dict[str, Any], Type[T]]]]
            The items matching the filter
        """
        filter_dict = filter_dict or {}

        return await self.document.find(filter_dict, *args, **kwargs).to_list(None)

    @return_converted
    async def find_by_id(
        self, data_id: Any
    ) -> Optional[Union[Dict[str, Any], Type[T]]]:
        """
        Find and return one item.

        Parameters
        ----------
        data_id: Any
            The _id of the item to find

        Returns
        -------
        Optional[Union[Dict[str, Any], Type[T]]]
            The result of the query
        """
        return await self.document.find_one({"_id": data_id})

    @return_converted
    async def find_by_custom(
        self, filter_dict: Dict[str, Any]
    ) -> Optional[Union[Dict[str, Any], Type[T]]]:
        """
        Find and return one item.

        Parameters
        ----------
        filter_dict: Dict[str, Any]
            What to filter/find based on

        Returns
        -------
        Optional[Union[Dict[str, Any], Type[T]]]
            The result of the query
        """
        self.__ensure_dict(filter_dict)

        return await self.document.find_one(filter_dict)  # type: ignore

    @return_converted
    async def find_many_by_custom(
        self, filter_dict: Dict[str, Any]
    ) -> List[Union[Dict[str, Any], Type[T]]]:
        """
        Find and return all items
        matching the given filter

        Parameters
        ----------
        filter_dict: Dict[str, Any]
            What to filter/find based on

        Returns
        -------
        List[Union[Dict[str, Any], Type[T]]]
            The result of the query
        """
        self.__ensure_dict(filter_dict)

        return await self.document.find(filter_dict).to_list(None)

    async def delete_by_id(self, data_id: Any) -> Optional[DeleteResult]:
        """
        Delete an item from the Document
        if an item with that _id exists

        Parameters
        ----------
        data_id: Any
            The _id to delete

        Returns
        -------
        Optional[DeleteResult]
            The result of deletion
        """
        if await self.find_by_id(data_id) is None:
            return None

        return await self.document.delete_many({"_id": data_id})

    async def delete_by_custom(
        self, filter_dict: Dict[str, Any]
    ) -> Optional[Union[List[DeleteResult], DeleteResult]]:
        """
        Delete an item from the Document
        matching the filter

        Parameters
        ----------
        filter_dict: Any
            Delete items matching this
            dictionary

        Returns
        -------
        Optional[DeleteResult]
            The result of deletion
        """
        self.__ensure_dict(filter_dict)

        return await self.document.delete_many(filter_dict)

    async def insert(self, data: Dict[str, Any]) -> None:
        """
        Insert the given data into the document

        Parameters
        ----------
        data: Dict[str, Any]
            The data to insert
        """
        self.__ensure_dict(data)

        await self.document.insert_one(data)

    async def upsert(
        self, data: Dict[str, Any], option: str = "set", *args: Any, **kwargs: Any
    ) -> None:
        """
        Performs an UPSERT operation,
        so data is either INSERTED or UPDATED
        based on the current state of the document.

        Parameters
        ----------
        data: Dict[str, Any]
            The data to upsert (filter is _id)
        option: str
            The optional option to pass to mongo,

            default is set

        """
        if await self.find_by_id(data["_id"]) is None:
            return await self.insert(data)

        await self.update_by_id(data, option, upsert=True, *args, **kwargs)

    async def update_by_id(
        self, data: Dict[str, Any], option: str = "set", *args: Any, **kwargs: Any
    ) -> None:
        """
        Performs an update operation.

        Parameters
        ----------
        data: Dict[str, Any]
            The data to upsert (filter is _id)
        option: str
            The optional option to pass to mongo,

            default is set
        """
        self.__ensure_dict(data)
        self.__ensure_id(data)

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
        """
        Performs an UPSERT operation,
        so data is either INSERTED or UPDATED
        based on the current state of the document.

        Uses filter_dict rather then _id

        Parameters
        ----------
        filter_dict: Dict[str, Any]
            The data to filter on
        update_data: Dict[str, Any]
            The data to upsert
        option: str
            The optional option to pass to mongo,

            default is set
        """
        if not bool(await self.find_by_custom(filter_dict)):
            # Insert
            return await self.insert({**filter_dict, **update_data})

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
        """
        Performs an update operation.

        Parameters
        ----------
        filter_dict: Dict[str, Any]
            The data to filter on
        update_data: Dict[str, Any]
            The data to upsert
        option: str
            The optional option to pass to mongo,

            default is set
        """
        self.__ensure_dict(filter_dict)
        self.__ensure_dict(update_data)

        # Update
        await self.document.update_one(
            filter_dict, {f"${option}": update_data}, *args, **kwargs
        )

    async def unset(self, data: Dict[str, Any]) -> None:
        """
        Remove a given param, basically dict.pop on the db.

        Works based off _id

        Parameters
        ----------
        data: Dict[str, Any]
            The data

        Notes
        -----
        This is one of the least tested parts.

        """
        self.__ensure_dict(data)
        self.__ensure_id(data)

        # TODO This might break stuff now removed?
        # if await self.find_by_id(data["_id"]) is None:
        #     return

        data_id = data.pop("_id")
        await self.document.update_one({"_id": data_id}, {"$unset": data})

    async def increment(
        self, data_id: Any, amount: Union[int, float], field: str
    ) -> None:
        """
        Increment a field somewhere.

        Parameters
        ----------
        data_id: Any
            The _id of the 'thing' we want to increment
        amount: Union[int, float]
            How much to increment (or decrement) by
        field: str
            The key for the field to increment
        """
        # TODO Test removing this
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
