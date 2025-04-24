import csv

input_file = "neutral.txt"  # Input file containing posts separated by ---
output_file = "neutral.csv"  # Output CSV file

# Read the input file
with open(input_file, "r", encoding="utf-8") as infile:
    content = infile.read()

# Split the content by posts using "---" separator
posts = [post.strip() for post in content.split("---") if post.strip()]

# Debugging: Print the number of posts found
print(f"Total posts found: {len(posts)}")

# Write to the CSV file
with open(output_file, "w", encoding="utf-8", newline="") as outfile:
    writer = csv.writer(outfile, quoting=csv.QUOTE_ALL, lineterminator="\n")
    writer.writerow(["text"])  # Write header
    for post in posts:
        # Replace actual newlines with literal "\n" string
        formatted_post = post.replace("\n", "\\n")
        writer.writerow([formatted_post])

print(f"✅ Created {output_file} with {len(posts)} posts.")
