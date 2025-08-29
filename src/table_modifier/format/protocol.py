from typing import Protocol, Any, runtime_checkable, List

from src.table_modifier.file_interface.protocol import FileInterfaceProtocol


@runtime_checkable
class FormatProtocol(Protocol):
    """
    Describes the format of an output object.

    A format is a structured representation of data that includes components such as
    headers, footers, and file interfaces. It defines how data is organized and
    presented in a specific format, which can be used for reading and writing files.

    A format must implement the file_interface method to provide a file interface,
    metadata, and the components method to return a list of components that make up the
    format. Beyond that, methods are defined by which components are expected to be
    present in the format, such as header and footer.

    The metadata method provides additional information about the format, such as
    encoding, version, or any other relevant details that describe the format's
    characteristics and are necessary for processing the data correctly. For example,
    it might include information about the encoding used, or in the case of CSV files,
    it might specify the delimiter used in the file.

    The metadata method returns a dictionary that contains key-value pairs,
    where keys are metadata names and values are their corresponding values. The
    metadata is ment to be passed as an argument to the file interface
    when reading or writing files in the specified format.
    """
    def components(self) -> List[str]:
        """
        Returns a list of components that make up the format.
        Each component is a string representing a part of the format. The order of
        components is significant. For example, a format might have components like
        "header", "body", and "footer". The components should be returned in the order
        they appear in the format.

        Returns:
            List[str]: A list of format components.

        Examples:
        --------
        >>> class MyFormat:
        ...     def components(self) -> List[str]:
        ...         return ["header", "body", "footer"]
        """
        raise NotImplementedError("FormatProtocol must implement the components method.")

    def header(self) -> List[List[str]]:
        """
        Returns the header of the format.

        This can be either a single header row or multiple header rows,
        depending on the format's structure. The header is typically a list of lists,
        where each inner list represents a row in the header.

        The most standard format is a single header row, which is a list of strings
        where each string is a column name. However, some formats may have multiple
        header rows where any one of them can be considered the header.

        Returns:
            str: The header string.

        Examples:
        --------
        >>> class MyFormat:
        ...     def header(self) -> str:
        ...         return [["Column1", "Column2", "Column3"]]
        """
        raise NotImplementedError("FormatProtocol must implement the header method.")

    def footer(self) -> List[List[str]]:
        """
        Returns the footer of the format.

        The footer is typically a list of lists, where each inner list represents a row
        in the footer. The footer can be empty if the format does not require one.

        Returns:
            List[List[str]]: The footer rows.

        Examples:
        --------
        >>> class MyFormat:
        ...     def footer(self) -> List[List[str]]:
        ...         return [["Footer1", "Footer2"]]
        """
        raise NotImplementedError("FormatProtocol must implement the footer method.")

    def file_interface(self) -> FileInterfaceProtocol:
        """
        Returns the file interface associated with the format.

        The file interface provides methods for reading and writing files in the specified format.

        Returns:
            FileInterfaceProtocol: The file interface for the format.

        Examples:
        --------
        >>> class MyFormat:
        ...     def file_interface(self) -> FileInterfaceProtocol:
        ...         return MyFileInterface()
        """
        raise NotImplementedError("FormatProtocol must implement the file_interface method.")

    def metadata(self) -> dict[str, Any]:
        """
        Returns metadata about the format.

        Metadata can include information such as encoding, version, or any other relevant
        details that describe the format's characteristics and are necessary for processing
        the data correctly.

        Returns:
            dict[str, Any]: A dictionary containing metadata key-value pairs.

        Examples:
        --------
        >>> class MyFormat:
        ...     def metadata(self) -> dict[str, Any]:
        ...         return {"encoding": "utf-8", "version": "1.0"}
        """
        raise NotImplementedError("FormatProtocol must implement the metadata method.")

