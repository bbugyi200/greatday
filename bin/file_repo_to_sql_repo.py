"""This script migrates all greatday todos from text files to SQLite DB."""

from __future__ import annotations

import sys

from greatday._common import drop_word_if_startswith
from greatday._repo import FileRepo, SQLRepo


def main() -> int:
    """Main entry point for this script."""
    if len(sys.argv) != 3:
        print(
            "usage: file_repo_to_sql_repo DATA_DIR SQLITEDB", file=sys.stderr
        )
        return 2

    args = list(sys.argv[1:])
    data_dir = args.pop(0)
    sqlite_db = args.pop(0)

    file_repo = FileRepo(data_dir)
    sql_repo = SQLRepo(f"sqlite:///{sqlite_db}")

    for todo in file_repo.todo_group:
        metadata = dict(todo.metadata.items())
        if "id" in metadata:
            metadata["oid"] = metadata["id"]
            del metadata["id"]

        desc = drop_word_if_startswith(todo.desc, "id:")
        new_todo = todo.new(desc=desc, metadata=metadata)
        print(new_todo.to_line())
        sql_repo.add(new_todo).unwrap()
    return 0


if __name__ == "__main__":
    main()
