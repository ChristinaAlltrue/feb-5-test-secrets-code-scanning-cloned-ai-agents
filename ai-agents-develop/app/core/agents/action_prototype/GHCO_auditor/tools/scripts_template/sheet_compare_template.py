from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd


@dataclass
class SheetCompareResult:
    """Structured comparison result.

    Attributes:
        added_rows: Rows present in the new file but not in the old file.
        deleted_rows: Rows present in the old file but not in the new file.
        updated_rows: Rows where the update-identifying field changed for the same unique key(s).
        unique_columns: Columns used as the unique identifier across both files.
        update_identify_column: Column used to detect updates (changes in values).
        old_file_date: Parsed datetime for the old file (for context/metadata only).
        new_file_date: Parsed datetime for the new file (for context/metadata only).
    """

    added_rows: pd.DataFrame
    deleted_rows: pd.DataFrame
    updated_rows: pd.DataFrame
    unique_columns: list[str]
    update_identify_column: Optional[str]
    old_file_date: datetime
    new_file_date: datetime


def _parse_date(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return value
    # Expecting ISO-8601 like strings (e.g. "2025-02-24").
    return datetime.fromisoformat(value)


def _read_dataframe(file_path: str | Path) -> pd.DataFrame:
    file_path = str(file_path)
    if file_path.lower().endswith(".csv"):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)

    # Drop all-empty columns and normalize column names
    df.dropna(axis=1, how="all", inplace=True)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _apply_header_row(
    df: pd.DataFrame, header_row_index: Optional[int]
) -> pd.DataFrame:
    if header_row_index is None:
        return df
    if header_row_index < 0 or header_row_index >= len(df):
        raise ValueError(
            f"header_row_index {header_row_index} is out of bounds for dataframe with {len(df)} rows"
        )
    new_columns = df.iloc[header_row_index].tolist()
    df = df.drop(index=header_row_index).copy()
    df.columns = [str(c).strip() for c in new_columns]
    df.dropna(how="all", inplace=True)
    return df


def _ensure_columns_exist(
    df: pd.DataFrame, columns: Iterable[str], *, label: str
) -> None:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing columns {missing} in {label}. Available columns: {df.columns.tolist()}"
        )


def _ensure_unique_key(
    df: pd.DataFrame, unique_columns: list[str], *, label: str
) -> None:
    combined = df[unique_columns].apply(lambda row: tuple(row), axis=1)
    if not combined.is_unique:
        raise ValueError(
            f"Combination of columns {unique_columns} is not unique in {label}"
        )
    # Ensure hashability to match downstream merging behavior
    try:
        _ = combined.apply(hash)
    except TypeError as exc:
        raise ValueError(
            f"Values in combination of columns {unique_columns} are not hashable in {label}"
        ) from exc


def _maybe_split_update_column(
    df: pd.DataFrame,
    update_identify_column: Optional[str],
    update_delimiter: Optional[str],
) -> pd.DataFrame:
    if not update_identify_column or not update_delimiter:
        return df

    if update_delimiter in ("(", ")", "[", "]", "{", "}"):
        raise ValueError(
            f"Delimiter {update_delimiter} is not allowed. Choose a simple delimiter like ',' or ';'"
        )

    if update_identify_column not in df.columns:
        raise ValueError(
            f"Update identify column '{update_identify_column}' not found in dataframe."
        )

    def split_and_normalize(value):
        if isinstance(value, list) or isinstance(value, tuple):
            return tuple(sorted({str(v).strip() for v in value}))
        if pd.isna(value):
            return value
        parts = str(value).split(update_delimiter)
        return tuple(sorted({p.strip() for p in parts}))

    df = df.copy()
    df[update_identify_column] = df[update_identify_column].apply(split_and_normalize)
    return df


def _compare_added_rows(
    old_df: pd.DataFrame, new_df: pd.DataFrame, unique_columns: list[str]
) -> pd.DataFrame:
    merged = new_df.merge(old_df, on=unique_columns, how="left", indicator=True)
    add_keys = merged[merged["_merge"] == "left_only"][unique_columns]
    result = new_df.merge(add_keys, on=unique_columns, how="inner")
    # Preserve original column order
    return result[new_df.columns]


def _compare_deleted_rows(
    old_df: pd.DataFrame, new_df: pd.DataFrame, unique_columns: list[str]
) -> pd.DataFrame:
    merged = old_df.merge(new_df, on=unique_columns, how="left", indicator=True)
    del_keys = merged[merged["_merge"] == "left_only"][unique_columns]
    result = old_df.merge(del_keys, on=unique_columns, how="inner")
    return result[old_df.columns]


def _compare_updated_rows(
    old_df: pd.DataFrame,
    new_df: pd.DataFrame,
    unique_columns: list[str],
    update_identify_column: Optional[str],
) -> pd.DataFrame:
    if not update_identify_column:
        # If no update-identify column specified, there are no meaningful "updates"
        return pd.DataFrame(columns=unique_columns)

    _ensure_columns_exist(old_df, [update_identify_column], label="old_df")
    _ensure_columns_exist(new_df, [update_identify_column], label="new_df")

    merged = old_df.merge(new_df, on=unique_columns, suffixes=("_old", "_new"))

    def values_differ(row) -> bool:
        left = row[f"{update_identify_column}_old"]
        right = row[f"{update_identify_column}_new"]
        try:
            # Handle tuple/list encoded values as sets for order-insensitive comparison
            if isinstance(left, (list, tuple)) or isinstance(right, (list, tuple)):
                left_set = set(left if isinstance(left, (list, tuple)) else [left])
                right_set = set(right if isinstance(right, (list, tuple)) else [right])
                return left_set != right_set
            # Fallback to direct comparison (NaN-safe)
            if pd.isna(left) and pd.isna(right):
                return False
            return left != right
        except Exception:
            return left != right

    changed = merged[merged.apply(values_differ, axis=1)]
    cols = unique_columns + [
        f"{update_identify_column}_old",
        f"{update_identify_column}_new",
    ]
    return changed[cols]


def compare_sheets(
    old_file_path: str | Path,
    new_file_path: str | Path,
    old_file_date: datetime | str,
    new_file_date: datetime | str,
    *,
    unique_columns: Optional[list[str]] = None,
    update_identify_column: Optional[str] = None,
    update_delimiter: Optional[str] = None,
    old_header_row_index: Optional[int] = None,
    new_header_row_index: Optional[int] = None,
) -> SheetCompareResult:
    """Compare two tabular files and detect added, deleted, and updated rows.

    This function reads two datasets (CSV or Excel), validates the provided unique keys,
    and optionally splits values in the update-identify column using a delimiter to support
    set-like comparisons (e.g., role lists). It returns dataframes for added, deleted, and
    updated rows, plus metadata.

    Parameters:
        old_file_path: Path to the old dataset (CSV or Excel).
        new_file_path: Path to the new dataset (CSV or Excel).
        old_file_date: Date for the old file; accepts datetime or ISO string (e.g., "2024-07-03").
        new_file_date: Date for the new file; accepts datetime or ISO string (e.g., "2025-02-24").
        unique_columns: Columns that uniquely identify a row across both files. REQUIRED.
        update_identify_column: Column used to detect updates when its value changes.
        update_delimiter: Optional delimiter for splitting update column values into sets (e.g., ",").
        old_header_row_index: If provided, use this row from the old file as the header row.
        new_header_row_index: If provided, use this row from the new file as the header row.

    Returns:
        SheetCompareResult: Dataclass holding added, deleted, and updated rows and metadata.

    Usage:
        >>> from datetime import datetime
        >>> result = compare_sheets(
        ...     old_file_path="./test_data/ACME-User-List-Old.xlsx",
        ...     new_file_path="./test_data/ACME-User-List-New.xlsx",
        ...     old_file_date="2024-07-03",
        ...     new_file_date="2025-02-24",
        ...     unique_columns=["Email"],
        ...     update_identify_column="Groups",
        ...     update_delimiter=",",
        ... )
        >>> result.added_rows.head()
        >>> result.deleted_rows.head()
        >>> result.updated_rows.head()

    Notes:
        - If your files have a non-standard header row, set old_header_row_index/new_header_row_index.
        - For string lists in the update column (e.g., "role1, role2"), set update_delimiter to
          compare as sets and ignore order/duplicates.
    """

    if unique_columns is None or len(unique_columns) == 0:
        raise ValueError("unique_columns is required and cannot be empty")

    if update_identify_column and update_identify_column in unique_columns:
        raise ValueError(
            f"update_identify_column '{update_identify_column}' must not be among unique_columns {unique_columns}"
        )

    old_dt = _parse_date(old_file_date)
    new_dt = _parse_date(new_file_date)

    old_df = _read_dataframe(old_file_path)
    new_df = _read_dataframe(new_file_path)

    old_df = _apply_header_row(old_df, old_header_row_index)
    new_df = _apply_header_row(new_df, new_header_row_index)

    _ensure_columns_exist(old_df, unique_columns, label="old_df")
    _ensure_columns_exist(new_df, unique_columns, label="new_df")
    _ensure_unique_key(old_df, unique_columns, label="old_df")
    _ensure_unique_key(new_df, unique_columns, label="new_df")

    # Normalize update column if requested
    if update_identify_column:
        _ensure_columns_exist(old_df, [update_identify_column], label="old_df")
        _ensure_columns_exist(new_df, [update_identify_column], label="new_df")
        old_df = _maybe_split_update_column(
            old_df, update_identify_column, update_delimiter
        )
        new_df = _maybe_split_update_column(
            new_df, update_identify_column, update_delimiter
        )

    added = _compare_added_rows(old_df, new_df, unique_columns)
    deleted = _compare_deleted_rows(old_df, new_df, unique_columns)
    updated = _compare_updated_rows(
        old_df, new_df, unique_columns, update_identify_column
    )

    return SheetCompareResult(
        added_rows=added,
        deleted_rows=deleted,
        updated_rows=updated,
        unique_columns=list(unique_columns),
        update_identify_column=update_identify_column,
        old_file_date=old_dt,
        new_file_date=new_dt,
    )


if __name__ == "__main__":
    # Example run (adjust paths as needed)
    demo = compare_sheets(
        old_file_path="./test_data/ACME-User-List-Old.xlsx",
        new_file_path="./test_data/ACME-User-List-New.xlsx",
        old_file_date="2024-07-03",
        new_file_date="2025-02-24",
        unique_columns=["Email"],
        update_identify_column="Groups",
        update_delimiter=",",
    )
    print("Added:", demo.added_rows.head(3))
    print("Deleted:", demo.deleted_rows.head(3))
    print("Updated:", demo.updated_rows.head(3))
