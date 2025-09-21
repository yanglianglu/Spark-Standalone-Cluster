import pathlib
import shutil

TARGETS = [
    pathlib.Path("data/warehouse"),
    pathlib.Path("data/metastore_db"),
]


def remove_path(target: pathlib.Path) -> None:
    if not target.exists():
        return
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()


def main() -> None:
    for target in TARGETS:
        remove_path(target)


if __name__ == "__main__":
    main()
