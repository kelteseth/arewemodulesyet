import os
import sys
import json
import argparse
import yaml
import time
from datetime import datetime
from git import Repo
from termcolor import colored

def get_git_revision_count(repo, file_path):
    try:
        # Get count of commits affecting the file
        return len(list(repo.iter_commits(paths=file_path)))
    except Exception as e:
        print(colored(f"Error retrieving revisions for {file_path}: {str(e)}", "red"))
        return 0

def read_vcpkg_json(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return {
            "name": data.get("name", "Unknown"),
            "version": data.get("version-string", data.get("version", "Unknown")),
            "homepage": data.get("homepage", ""),
            # The follwing are empty and getting overwritten by hand
            "current_min_cpp_version": "Unknown",
            "tracking_issue": "", # Issue that tracks the progress
            "modules_support_date": 0,  # Unix timestamp, default 0
            "help_wanted": "❔"
        }
    except Exception as e:
        print(colored(f"Error reading {json_path}: {str(e)}", "red"))
        return None
     
 
# Two modes:
# 1. Merge raw_progress.yml and progress_overwrite.yml into progress.yml
# 2. Parse vcpkg repo data into raw_progress.yml 🐌 this will take some time!
def main():
    parser = argparse.ArgumentParser(description="Process the vcpkg repository to extract package details and revision counts.")
    parser.add_argument("--repo_path", type=str, help="Path to the vcpkg repository.")
    parser.add_argument("--merge", action="store_true", help="Only merges raw_progress.yml and progress_overwrite.yml into progress.yml  .")
    args = parser.parse_args()

    if args.merge:
        
        base_path = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(base_path, "data")
        
        load_and_merge_yaml(f'{script_path}/raw_progress.yml', f'{script_path}/progress_overwrite.yml', f'{script_path}/progress.yml')
    else:
        prase(args.repo_path)

def load_and_merge_yaml(file1, file2, output_file):
    print("\n ",file1, "\n ",file2,"\n ",output_file)
    with open(file1, 'r', encoding='utf-8') as f:
        raw_progress = yaml.safe_load(f)
    
    with open(file2, 'r', encoding='utf-8') as f:
        progress_overwrite = yaml.safe_load(f)
    
    # Assuming overwrite data doesn't have a header and directly contains ports
    overwrite_ports = progress_overwrite['ports']
    # Create a dictionary from the overwrite ports data for easy access
    overwrite_dict = {item['name']: item for item in overwrite_ports}
    
    # Extract the raw ports data
    raw_ports = raw_progress['header']
    raw_ports_list = raw_progress['ports']
    
    # Merge the data
    merged_ports = []
    for item in raw_ports_list:
        if item['name'] in overwrite_dict:
            # Only overwrite specific fields
            for key in ['import_statement','current_min_cpp_version', 'tracking_issue', 'modules_support_date', 'help_wanted', 'status']:
                if key in overwrite_dict[item['name']]:
                    item[key] = overwrite_dict[item['name']][key]
        merged_ports.append(item)
    
    # Add project not listed in vcpkg
    ## Create a dictionary from the merged ports data for easy access
    merged_set = {item['name'] for item in merged_ports}
    for name,item in overwrite_dict.items():
        if name not in merged_set:
            merged_ports.append({
                "name": name,
                "current_min_cpp_version": item.get("current_min_cpp_version", "Unknown"),
                "help_wanted": item.get("help_wanted", "❔"),
                "homepage": item.get("homepage", ""),
                "modules_support_date": item.get("modules_support_date", "0"),
                "status": item.get("status", "?"),
                "tracking_issue": item.get("tracking_issue", ""),
                "version": item.get("version", ""),
                "import_statement": item.get("import_statement", "")
            })
    # Reconstruct the merged data with header
    merged_data = {
        'header': raw_ports,
        'ports': merged_ports
    }
    
    # Save the merged data back to a new YAML file with UTF-8 encoding
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.safe_dump(merged_data, f, allow_unicode=True)
 
def prase(repo_path):

    # Validate the repository path
    if not os.path.exists(repo_path) or not os.path.isdir(repo_path):
        print(colored("Provided repository path does not exist or is not a directory.", "red"))
        sys.exit(1)

    repo = Repo(repo_path)
    print(colored("Repository loaded successfully.", "blue"))

    # Path to the ports directory
    ports_dir = os.path.join(repo_path, 'ports')
    # List to store enhanced port data
    ports_data = []
    file_count = 0
    total_files = sum(1 for root, dirs, files in os.walk(ports_dir) if 'portfile.cmake' in files and 'vcpkg.json' in files)

    # Walk through the ports directory
    for root, dirs, files in os.walk(ports_dir):
        if 'portfile.cmake' in files:
            portfile_path = os.path.join(root, 'portfile.cmake')
            vcpkg_json_path = os.path.join(root, 'vcpkg.json')
            if os.path.exists(vcpkg_json_path):
                # Get the number of revisions for the portfile.cmake
                revisions = get_git_revision_count(repo, portfile_path)
                vcpkg_data = read_vcpkg_json(vcpkg_json_path)
                if vcpkg_data:
                    vcpkg_data['revision_count'] = revisions
                    vcpkg_data['status'] = "❔"
                    ports_data.append(vcpkg_data)
                    file_count += 1
                    print(f"\rProcessed {file_count}/{total_files} files...", end='', flush=True)

    # Ensure the output directory exists
    os.makedirs('./data', exist_ok=True)
    current_time = int(time.time())
    header_info = {
        'generated_date':  current_time,
        'vcpkg_commit_hash': repo.head.commit.hexsha
    }
    output_data = {'header': header_info, 'ports': ports_data}

    # Save to YAML file
    with open(f'./data/raw_progress.yml', 'w', encoding='utf-8') as yaml_file:
        yaml.dump(output_data, yaml_file, default_flow_style=False, allow_unicode=True)

    print("\n" + colored(f"Processed and saved details for {file_count} ports.", "blue"))

if __name__ == '__main__':
    main()
