import os
import sys
import json
import argparse
import yaml
import time
import shutil
import tempfile
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
            # The following are empty and getting overwritten by hand
            "current_min_cpp_version": "Unknown",
            "tracking_issue": "", # Issue that tracks the progress
            "modules_support_date": "",  # ISO 8601 date (YYYY-MM-DD), default empty
            "module_native": "", # Whether if the modules are used as a wrapper or natively
        }
    except Exception as e:
        print(colored(f"Error reading {json_path}: {str(e)}", "red"))
        return None

def main():
    parser = argparse.ArgumentParser(description="Process the vcpkg repository to extract package details and revision counts.")
    args = parser.parse_args()

    # Setup tmp directory for vcpkg clone in SYSTEM temp folder (completely isolated from project)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # Use system temp directory instead of project folder
    system_tmp = tempfile.gettempdir()
    repo_path = os.path.join(system_tmp, 'arewemodulesyet_vcpkg_clone')
    
    print(colored(f"Using system temp directory: {system_tmp}", "blue"))
    print(colored(f"Vcpkg will be cloned to: {repo_path}", "blue"))
    
    # Safety check: Ensure repo_path is NOT anywhere near the project
    project_root_abs = os.path.abspath(project_root)
    repo_path_abs = os.path.abspath(repo_path)
    
    if repo_path_abs.startswith(project_root_abs):
        print(colored("ERROR: Repo path is inside project directory! This should never happen.", "red"))
        sys.exit(1)
    
    # Additional safety: verify we're using actual system temp
    if not repo_path_abs.startswith(os.path.abspath(system_tmp)):
        print(colored("ERROR: Repo path is not in system temp directory!", "red"))
        sys.exit(1)
    
    # Clone or update vcpkg repository
    vcpkg_url = "https://github.com/microsoft/vcpkg.git"
    
    if os.path.exists(repo_path):
        print(colored(f"Updating existing vcpkg repository at {repo_path}...", "blue"))
        try:
            repo = Repo(repo_path)
            origin = repo.remotes.origin
            origin.fetch()
            repo.git.reset('--hard', 'origin/master')
            print(colored("Repository updated successfully.", "blue"))
        except Exception as e:
            print(colored(f"Error updating repository: {str(e)}", "red"))
            print(colored("Continuing with existing state...", "yellow"))
    else:
        print(colored(f"Cloning vcpkg repository to {repo_path}...", "blue"))
        os.makedirs(repo_path, exist_ok=True)
        repo = Repo.clone_from(vcpkg_url, repo_path, branch='master')
        print(colored("Repository cloned successfully.", "blue"))

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
    data_dir = os.path.join(project_root, 'data', 'generated')
    os.makedirs(data_dir, exist_ok=True)
    
    current_time = int(time.time())
    header_info = {
        'generated_date':  current_time,
        'vcpkg_commit_hash': repo.head.commit.hexsha
    }
    output_data = {'header': header_info, 'ports': ports_data}

    # Save to YAML file with DO NOT EDIT header
    output_path = os.path.join(data_dir, 'vcpkg_packages.yml')
    header_comment = """###############################################################################
# DO NOT EDIT THIS FILE - IT IS AUTO-GENERATED
#
# This file is automatically generated by tools/generate_vcpkg_package_list.py
# from the vcpkg repository. Any manual changes will be overwritten.
#
# To modify package metadata, edit data/vcpkg_overrides.yml instead.
# To add non-vcpkg projects, edit data/external_projects.yml instead.
###############################################################################

"""
    with open(output_path, 'w', encoding='utf-8') as yaml_file:
        yaml_file.write(header_comment)
        yaml.dump(output_data, yaml_file, default_flow_style=False, allow_unicode=True)

    print("\n" + colored(f"Processed and saved details for {file_count} ports to {output_path}", "blue"))

if __name__ == '__main__':
    main()
