#!/bin/zsh
set -euo pipefail

ROOT="${0:A:h:h:h}"
WEZTERM="${WEZTERM_BIN:-/opt/homebrew/bin/wezterm}"
OUTPUT="${1:-$ROOT/artifacts/decisioning/feature_aware_ga/full_2m}"
CHUNK_SIZE="${CHUNK_SIZE:-50000}"

if [[ ! -x "$WEZTERM" ]]; then
  print -u2 "WezTerm executable not found: $WEZTERM"
  exit 1
fi
if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  print -u2 "Python environment not found: $ROOT/.venv/bin/python"
  exit 1
fi

mkdir -p "$OUTPUT"
touch "$OUTPUT/wezterm.log" "$OUTPUT/status.json"

printf -v root_q '%q' "$ROOT"
printf -v output_q '%q' "$OUTPUT"
printf -v log_q '%q' "$OUTPUT/wezterm.log"
printf -v status_q '%q' "$OUTPUT/status.json"

pipeline_pane="$($WEZTERM cli spawn --cwd "$ROOT")"
pipeline_command="cd $root_q && .venv/bin/python -m experiments.code.run_full_feature_aware_ga_pipeline --stage all --chunk-size $CHUNK_SIZE --output $output_q 2>&1 | tee -a $log_q"
$WEZTERM cli send-text --pane-id "$pipeline_pane" --no-paste "$pipeline_command"$'\n'

log_pane="$($WEZTERM cli spawn --cwd "$ROOT")"
$WEZTERM cli send-text --pane-id "$log_pane" --no-paste "tail -n 80 -F $log_q"$'\n'

status_pane="$($WEZTERM cli spawn --cwd "$ROOT")"
$WEZTERM cli send-text --pane-id "$status_pane" --no-paste "tail -n 20 -F $status_q"$'\n'

print "Full feature-aware workflow launched"
print "  pipeline pane: $pipeline_pane"
print "  log pane:      $log_pane"
print "  status pane:   $status_pane"
print "  output:        $OUTPUT"
print "  resume:        rerun this launcher; validated chunks are skipped"