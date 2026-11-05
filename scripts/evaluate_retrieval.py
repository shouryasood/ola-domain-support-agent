from __future__ import annotations

from collections import defaultdict

from ola_support.rag.evaluation import evaluate


def main() -> None:
    rows = evaluate()
    totals = defaultdict(lambda: {"precision": 0.0, "recall": 0.0, "count": 0})

    for row in rows:
        print(
            f"{row['collection']} | {row['query']} | "
            f"P={row['precision_arithmetic']}={row['precision']:.3f} | "
            f"R={row['recall_arithmetic']}={row['recall']:.3f}"
        )
        summary = totals[row["collection"]]
        summary["precision"] += row["precision"]
        summary["recall"] += row["recall"]
        summary["count"] += 1

    print("\nStrategy averages:")
    for collection, summary in totals.items():
        count = summary["count"]
        print(
            f"{collection}: "
            f"mean precision={summary['precision'] / count:.3f}, "
            f"mean recall={summary['recall'] / count:.3f}"
        )


if __name__ == "__main__":
    main()
