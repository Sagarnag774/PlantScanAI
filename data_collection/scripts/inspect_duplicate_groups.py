import csv

INPUT_FILE = "datasets/reports/exact_duplicate_groups.csv"


def show_groups(condition, title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        count = 0

        for row in reader:
            if condition(row):
                count += 1

                print(f"\nGROUP {row['group_id']}")
                print(f"Files      : {row['group_size']}")
                print(f"Redundant  : {row['redundant_files']}")
                print(f"Datasets   : {row['datasets']}")
                print(f"Subsets    : {row['subsets']}")
                print(f"Splits     : {row['splits']}")
                print(f"Labels     : {row['labels']}")
                print(f"Files:")
                print(row["files"])

        print(f"\nTotal groups: {count}")


def main():

    show_groups(
        lambda row: row["split_leakage"] == "YES",
        "SPLIT LEAKAGE GROUPS",
    )

    show_groups(
        lambda row: row["label_conflict"] == "YES",
        "LABEL CONFLICT GROUPS",
    )


if __name__ == "__main__":
    main()