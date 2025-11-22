# Are we modules yet? Not even close, lol.

This website will track the most popular C++ projects, compilers and build systems. We use vcpkg to get a rough idea on how popular a library is via how many revisions the port has. For more information, checkout the python script that parses the data: `generate_vcpkg_usage_stats.py`.  

## Legend for `progress_overwrite.yml`

Example port 
``` yml
ports: 
- name: fmt
  # Can be different from lib name. For example vulkan-cpp uses vulkan_cpp!
  # `fmt` becomes: `import fmt;`
  import_statement: fmt
  # Date since when the lib has modules support. Used for extrapolating finish date (YYYY/M/DD)
  modules_support_date: 2024/5/22 
  status: ✅
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

### Dependencies
1. [Install Hugo Extended](https://gohugo.io/)
    -  🪟 `winget install Hugo.Hugo.Extended`
    -  🐧 & 🍏 [Download on Github](https://github.com/gohugoio/hugo/releases)
1. [Python 3 via uv](https://docs.astral.sh/uv/)
    -  🪟 `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
    -  🐧 & 🍏 `curl -LsSf https://astral.sh/uv/install.sh | sh`

### How to contribute

Edit `data/progress_overwrite.yml` if you want to update status or add new entries which doesn't
have a vcpkg entry. Edit `data/raw_progress.yml` if you want to add/delete entries.

Then execute the following commands to generate `progress.yml` and update `static/data/cumulative_stats.json`:

```bash
uv run  tools/merge_vcpkg_package_list_progress.py
uv run  tools/compute_completion_status.py
```

It will be appreciated if you can run `hugo serve` to check your change.

For other documents, see contents in `content`.

### Optionally regenerate raw_progress.yml
```bash
uv run  tools/generate_vcpkg_package_list.py
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
