import os
import re
import argparse

# Configuration
ROOT_DIR = r"."
INCLUDE_REGEX = re.compile(r'#include\s+"([^"]+)"')
# Persistent storage for "Apply to All" choices
CHOICE_CACHE = {}

def get_all_files(root_dir):
    file_map = {}
    for root, _, files in os.walk(root_dir):
        for f in files:
            file_map.setdefault(f, []).append(os.path.join(root, f))
    return file_map

def resolve_path(file_path, included_filename, locations, root):
    if included_filename in CHOICE_CACHE:
        return CHOICE_CACHE[included_filename]

    print(f"\nAmbiguity found in {file_path}")
    print(f"Include: {included_filename}")
    print("Candidates:")
    for i, loc in enumerate(locations):
        print(f"  {i}: {loc}")
    
    while True:
        try:
            user_input = input("Enter index of the correct candidate (or -1 to skip, index + 'A' to Apply to All): ")
            
            apply_to_all = False
            if user_input.upper().endswith('A'):
                apply_to_all = True
                choice = int(user_input[:-1])
            else:
                choice = int(user_input)

            if choice == -1:
                return None
            
            if 0 <= choice < len(locations):
                new_path = os.path.relpath(locations[choice], root).replace("\\", "/")
                if apply_to_all:
                    CHOICE_CACHE[included_filename] = new_path
                return new_path
            else:
                print("Invalid index. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number (optionally followed by 'A').")

def analyze_and_fix(root_dir, dry_run=True):
    file_map = get_all_files(root_dir)
    
    for root, _, files in os.walk(root_dir):
        for filename in files:
            file_path = os.path.join(root, filename)
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            new_content = content
            modified = False
            
            for match in INCLUDE_REGEX.finditer(content):
                included_path = match.group(1)
                included_filename = os.path.basename(included_path)
                
                if not os.path.exists(os.path.join(root, included_path)):
                    if included_filename in file_map:
                        locations = file_map[included_filename]
                        
                        if len(locations) == 1:
                            new_path = os.path.relpath(locations[0], root).replace("\\", "/")
                            new_content = new_content.replace(match.group(0), f'#include "{new_path}"')
                            modified = True
                        else:
                            new_path = resolve_path(file_path, included_filename, locations, root)
                            if new_path:
                                new_content = new_content.replace(match.group(0), f'#include "{new_path}"')
                                modified = True
            
            if modified:
                if dry_run:
                    print(f"[DRY RUN] Would fix: {file_path}")
                else:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Fixed: {file_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze and fix include paths.")
    parser.add_argument("--apply", action="store_true", help="Apply the changes to files.")
    args = parser.parse_args()
    
    dry_run = not args.apply
    if dry_run:
        print("Running in Dry-Run mode. Use --apply to save changes.")
    else:
        print("Running in Apply mode. Changes will be saved.")
        
    analyze_and_fix(ROOT_DIR, dry_run=dry_run)
