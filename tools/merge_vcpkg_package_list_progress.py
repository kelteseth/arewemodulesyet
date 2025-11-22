import os
import argparse
import yaml
from datetime import datetime

def load_and_merge_yaml(file1, file2, output_file):
    print("\n ", file1, "\n ", file2, "\n ", output_file)
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
            for key in ['import_statement', 'current_min_cpp_version', 'tracking_issue', 'modules_support_date', 'status', 'module_native']:
                if key in overwrite_dict[item['name']]:
                    item[key] = overwrite_dict[item['name']][key]
        merged_ports.append(item)
    
    # Add project not listed in vcpkg
    ## Create a dictionary from the merged ports data for easy access
    merged_set = {item['name'] for item in merged_ports}
    for name, item in overwrite_dict.items():
        if name not in merged_set:
            merged_ports.append({
                "name": name,
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
    raw_ports['total_projects'] = total_projects
    raw_ports['completed_projects'] = completed_projects
    raw_ports['progress_percent'] = round(progress_percent, 2)
    if estimated_completion_date:
        raw_ports['estimated_completion_date'] = estimated_completion_date
    
    # Reconstruct the merged data with header
    merged_data = {
        'header': raw_ports,
        'ports': merged_ports
    }
    
    # Save the merged data back to a new YAML file with UTF-8 encoding
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.safe_dump(merged_data, f, allow_unicode=True)

def main():
    parser = argparse.ArgumentParser(description="Merge raw_progress.yml and progress_overwrite.yml into progress.yml")
    args = parser.parse_args()
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(os.path.dirname(base_path), 'data')
    
    raw_progress_path = os.path.join(data_path, 'raw_progress.yml')
    progress_overwrite_path = os.path.join(data_path, 'progress_overwrite.yml')
    progress_path = os.path.join(data_path, 'progress.yml')
    
    load_and_merge_yaml(raw_progress_path, progress_overwrite_path, progress_path)

if __name__ == '__main__':
    main()
