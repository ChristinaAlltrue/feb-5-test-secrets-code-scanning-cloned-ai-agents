from pydantic import BaseModel, Field


class SheetCompareDeps(BaseModel):
    file_path_list: list[str] = Field(
        ...,
        description="List of file paths to compare",
        json_schema_extra={"example": ["file1.xlsx", "file2.xlsx"]},
    )
    instructions: str = Field(
        ...,
        description="Instructions for the sheet compare",
        json_schema_extra={
            "example": "Compare the two sheets and return the differences"
        },
    )


class SheetCompareResult(BaseModel):
    file_name: str = Field(
        ...,
        description="File name of the compare result. You must only return the file names, not the file paths.",
        json_schema_extra={"example": "file1.xlsx"},
    )
    file_description: str = Field(
        ...,
        description="Description of each file",
        json_schema_extra={
            "example": "The file 'added.csv' contains new users, 'removed.csv' contains users no longer in the list, and 'changed.csv' contains users whose details have changed."
        },
    )


class SheetCompareOutput(BaseModel):
    compare_results: list[SheetCompareResult] = Field(
        ...,
        description="List of compare results",
        json_schema_extra={
            "example": [
                {
                    "file_name": "added_rows.csv",
                    "description": "The added rows are in the file",
                }
            ]
        },
    )
    approach: str = Field(
        ...,
        description="""
        Describe the approach used to compare the sheets and the thinking behind it, like:
        - which file is the base file you chose as the base file
        - which column was chosen as the primary key
        - which column was chosen as the update identifier
        """,
        json_schema_extra={
            "example": "I chose the file 'ACME-User-List-Old.xlsx' as the base file, and the column 'email' as the primary key, and the column 'role' as the update identifier."
        },
    )
