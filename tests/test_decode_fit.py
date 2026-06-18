from fitparse import FitFile
from pathlib import Path


def dump_fit(path: Path) -> None:
    print("=" * 80)
    print(path)
    print("size:", path.stat().st_size)

    fitfile = FitFile(str(path))

    for msg in fitfile.get_messages():
        print(f"\n[{msg.name}]")
        for field in msg:
            print(f"  {field.name}: {field.value}")


dump_fit(Path("planned_workouts") / "116712038.fit")