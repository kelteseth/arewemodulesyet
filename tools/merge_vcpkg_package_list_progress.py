import os
import argparse
import yaml
from datetime import datetime
from termcolor import colored

def load_and_merge_yaml(vcpkg_packages_file, vcpkg_overrides_file, external_projects_file, output_file):
    print()
    print(colored("📦 Merging C++ modules progress data...", "cyan", attrs=["bold"]))
    print()
    print(colored("  Input files:", "blue"))
    print(f"    • vcpkg_packages:   {colored(vcpkg_packages_file, 'white')}")
    print(f"    • vcpkg_overrides:  {colored(vcpkg_overrides_file, 'white')}")
    print(f"    • external_projects: {colored(external_projects_file, 'white')}")
    print()
    
    with open(vcpkg_packages_file, 'r', encoding='utf-8') as f:
        vcpkg_packages = yaml.safe_load(f)
    
    with open(vcpkg_overrides_file, 'r', encoding='utf-8') as f:
        vcpkg_overrides = yaml.safe_load(f)
    
    with open(external_projects_file, 'r', encoding='utf-8') as f:
        external_projects = yaml.safe_load(f)
    
    # Create a dictionary from the overrides data for easy access
    overrides_ports = vcpkg_overrides.get('ports', [])
    overrides_dict = {item['name']: item for item in overrides_ports}
    
    # Extract the vcpkg packages data
    header_info = vcpkg_packages['header']
    vcpkg_ports_list = vcpkg_packages['ports']
    
    # Merge vcpkg packages with overrides
    merged_ports = []
    for item in vcpkg_ports_list:
        if item['name'] in overrides_dict:
            # Only overwrite specific fields
            for key in ['import_statement', 'current_min_cpp_version', 'tracking_issue', 'modules_support_date', 'status', 'module_native']:
                if key in overrides_dict[item['name']]:
                    item[key] = overrides_dict[item['name']][key]
        merged_ports.append(item)
    
    # Add external projects (not in vcpkg)
    external_ports = external_projects.get('projects', [])
    for item in external_ports:
        merged_ports.append({
            "name": item.get("name", "Unknown"),
            "current_min_cpp_version": item.get("current_min_cpp_version", "Unknown"),
            "homepage": item.get("homepage", ""),
            "modules_support_date": item.get("modules_support_date", ""),
            "status": item.get("status", "?"),
            'module_native': item.get("module_native", ""),
            "tracking_issue": item.get("tracking_issue", ""),
            "version": item.get("version", ""),
            "import_statement": item.get("import_statement", "")
        })
    
    # Calculate progress statistics
    total_projects = len(merged_ports)
    completed_projects = sum(1 for item in merged_ports if item.get('status') == '✅')
    progress_percent = (completed_projects / total_projects * 100) if total_projects > 0 else 0
    
    # Collect dates for projects with modules support
    modules_support_dates = [
        item['modules_support_date'] 
        for item in merged_ports 
        if item.get('status') == '✅' and item.get('modules_support_date', '').strip()
    ]
    
    # Calculate estimated completion date
    estimated_completion_date = None
    if modules_support_dates:
        try:
            # Parse dates in format "2020/6/23"
            timestamps = []
            for date_str in modules_support_dates:
                parts = date_str.split('/')
                if len(parts) == 3:
                    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                    timestamps.append(datetime(year, month, day).timestamp())
            
            if timestamps:
                oldest_timestamp = min(timestamps)
                current_timestamp = datetime.now().timestamp()
                months_passed = (current_timestamp - oldest_timestamp) / (30 * 24 * 3600)
                
                if months_passed > 0:
                    monthly_rate = len(timestamps) / months_passed
                    remaining_projects = total_projects - completed_projects
                    months_to_completion = remaining_projects / monthly_rate
                    estimated_completion_timestamp = current_timestamp + months_to_completion * 30 * 24 * 3600
                    estimated_completion_date = datetime.fromtimestamp(estimated_completion_timestamp).strftime('%Y-%m-%d')
        except Exception as e:
            print(f"Warning: Could not calculate estimated completion date: {e}")
    
    # Add progress stats to header
    header_info['total_projects'] = total_projects
    header_info['completed_projects'] = completed_projects
    header_info['progress_percent'] = round(progress_percent, 2)
    if estimated_completion_date:
        header_info['estimated_completion_date'] = estimated_completion_date
    
    # Reconstruct the merged data with header
    merged_data = {
        'header': header_info,
        'ports': merged_ports
    }
    
    # Save the merged data back to a new YAML file with UTF-8 encoding
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.safe_dump(merged_data, f, allow_unicode=True)
    
    # Print summary
    print(colored("  Output:", "blue"))
    print(f"    • {colored(output_file, 'white')}")
    print()
    print(colored("  Statistics:", "blue"))
    print(f"    • Total projects:     {colored(str(total_projects), 'yellow')}")
    print(f"    • With modules (✅):  {colored(str(completed_projects), 'green')}")
    print(f"    • Progress:           {colored(f'{progress_percent:.1f}%', 'cyan')}")
    if estimated_completion_date:
        print(f"    • Est. completion:    {colored(estimated_completion_date, 'magenta')}")
    print()
    print(colored("✅ Done!", "green", attrs=["bold"]))
    print()

def main():
    parser = argparse.ArgumentParser(description="Merge vcpkg_packages.yml, vcpkg_overrides.yml, and external_projects.yml into progress.yml")
    args = parser.parse_args()
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(os.path.dirname(base_path), 'data')
    generated_path = os.path.join(data_path, 'generated')
    
    # Ensure generated directory exists
    os.makedirs(generated_path, exist_ok=True)
    
    vcpkg_packages_path = os.path.join(generated_path, 'vcpkg_packages.yml')
    vcpkg_overrides_path = os.path.join(data_path, 'vcpkg_overrides.yml')
    external_projects_path = os.path.join(data_path, 'external_projects.yml')
    progress_path = os.path.join(data_path, 'progress.yml')
    
    load_and_merge_yaml(vcpkg_packages_path, vcpkg_overrides_path, external_projects_path, progress_path)

if __name__ == '__main__':
    main()
