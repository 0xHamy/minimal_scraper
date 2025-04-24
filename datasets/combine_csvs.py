import csv
import os

# Input CSV files
input_files = {
    "negative.csv": "negative",
    "positive.csv": "positive",
    "neutral.csv": "neutral"
}
output_file = "base.csv"

# List to store all rows (text, label)
all_rows = []

# Read each input CSV file
for file_path, label in input_files.items():
    if not os.path.exists(file_path):
        print(f"⚠️ {file_path} not found, skipping...")
        continue
    
    with open(file_path, "r", encoding="utf-8", newline="") as infile:
        reader = csv.reader(infile)
        header = next(reader, None)  # Skip header ("text")
        if header != ["text"]:
            print(f"⚠️ Unexpected header in {file_path}: {header}, expected ['text']")
            continue
        
        # Read each row and pair with label
        for row in reader:
            if row and len(row) == 1:
                text = row[0]
                all_rows.append([text, label])
            else:
                print(f"⚠️ Skipping malformed row in {file_path}: {row}")

# Write to base.csv
with open(output_file, "w", encoding="utf-8", newline="") as outfile:
    writer = csv.writer(outfile, quoting=csv.QUOTE_ALL, lineterminator="\n")
    writer.writerow(["text", "label"])
    for row in all_rows:
        writer.writerow(row)

print(f"✅ Created {output_file} with {len(all_rows)} rows.")
