# Are we modules yet? Not even close, lol.

This website will track the most popular C++ projects, compilers and build systems. We use vcpkg to get a rough idea on how popular a library is via how many revisions the port has. For more information, checkout the python script that parses the data: `generate_vcpkg_usage_stats.py`.  

## Legend for `progress_overwrite.yml`

Example port 
``` yml
ports: 
- name: fmt
  # Can be different from lib name. For example vulkan-cpp uses vulkan_cpp!
  import_statement: fmt
  # Date since when the lib has modules support. Used for extrapolating finish date
  modules_support_date: 2024/5/22 
  status: ✅
  help_wanted: ❌
  current_min_cpp_version: 11
  # These are often multiple issues, but always try to link the main issue
  tracking_issue: "https://github.com/fmtlib/fmt/pull/3134"
```

Note that most projects do not even have an issue for tracking `modules` support. If so you would have to create one, so we can track it here.

### status
- ❔ Default: No set. Help wanted for every lib that has this status!
- ✅ Full support
- ⚙️ Worked on
- ⚠️ Reported
- ❌ Corresponding tracking issue was closed and no planned support anytime soon.
- 💀 Needs support old library/compiler/build tool to even start adding support for `modules`.
- 🤡 Maintainer does want to keep it oldschool. No plan to update anytime soon.

### help_wanted
- ✅ Yes
- ❌ No
- 💀 Does not allow outside contributions

### Dependencies
1. [Hugo](https://gohugo.io/)
1. [Python3](https://www.python.org/downloads/) and the `pip` dependencies below. 
1. Optional: Latest [vcpkg](https://github.com/microsoft/vcpkg)

```bash
# Install python dependencies
pip install pyyaml gitpython termcolor
# Start local hugo
hugo serve
# Update your progress_overwrite.yml and genererate progress.yml
# hugo will then automatically refresh
python.exe .\generate_vcpkg_usage_stats.py --merge
```

### How to contribute

Edit `data/progress_overwrite.yml` if you want to update status or add new entries which doesn't
have a vcpkg entry. Edit `data/raw_progress.yml` if you want to add/delete entries.

Then execute the following commands to generate `progress.yml` and update `static/data/cumulative_stats.json`:

```bash
python.exe .\generate_vcpkg_usage_stats.py --merge
python.exe .\compute_completion_status.py
```

It will be appreciated if you can run `hugo serve` to check your change.

For other documents, see contents in `content`.

### Optionally rengerate raw_progress.yml
```bash
python.exe generate_vcpkg_usage_stats.py --repo_path=C:\vcpkg
```

### Website structure
```
- /data
    - raw_progress.yml          # Raw parsed vcpkg list
    - progress_overwrite.yml    # Additional infos added by hand like status, progress
    - progress.yml              # Merged result that is displayed on the website
- /layouts/partials/
    - progress-module.html      # Diagram and table for the home page
- /content/
    - tools.md                  # Tools site
    - documents.md              # Documents site
    - examples.md               # Examples site
```
