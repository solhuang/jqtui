# jqtui

jqtui is a TUI for jq to easily read, explore, and search JSON data with jq.

### Features
- See the results as you type

# Installing

Install with `pip`:
```
pip install jqtui
```

Alternatively, install with [pipx](https://pypa.github.io/pipx/):
```
pipx install jqtui
```

# Usage

Run jqtui with a filename:
```
curl https://api.github.com/repos/solhuang/jqtui/commits -o commits.json
jqtui commits.json
```

Or run jqtui by piping the output from another command:
```
curl https://api.github.com/repos/solhuang/jqtui/commits | jqtui
```