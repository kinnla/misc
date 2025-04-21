import os
import re

def rewrite_tags(file_path):
    # Open the file
    with open(file_path, "r") as file:
        # Read the file contents
        contents = file.readlines()

    for i,line in enumerate(contents):
        # Search for frontmatter tags
        frontmatter_search = re.search(r"^tags: (\[.*\])", line)
        if frontmatter_search:
            # Get the frontmatter tags
            frontmatter_tags = frontmatter_search.group(1)
            # Replace the frontmatter tags with hashtags
            hashtags = "#" + frontmatter_tags.replace(", ", " #").strip("[]")
            # Delete the frontmatter line
            del contents[i]
            # Iterate until you find a line starting with #
            i+=1
            while i<len(contents) and not contents[i].startswith("#"):
                i+=1
            #Insert new line with hashtags just below the header
            contents.insert(i+1, hashtags+'\n')
            break

    # Write the modified contents back to the file
    with open(file_path, "w") as file:
        file.write("".join(contents))

def main():
    for file_name in os.listdir("."):
        if file_name.endswith(".md"):
            rewrite_tags(file_name)

if __name__ == "__main__":
    main()
