# mxcli --help capture (v0.26.0)

**Status:** deferred. `mxcli` is not installed on the researcher's machine; no
`--help` output has been captured here. The command inventory in
`docs/research/mxcli-inventory.md` was derived by reading the mxcli source at
tag `v0.26.0` (SHA `12ce281622a1a78ebb6737e61fe6b5ea78c59e45`), not from
`--help`.

When a machine with mxcli v0.26.0 installed is available, run the snippet below
to populate this directory. Each command listed is the exact set that
`cmd/mxcli/*.go` registers at this tag; every subcommand parent is included so
the top-level help also drops out as `root.txt`.

```bash
set -euo pipefail
cd "$(dirname "$0")"

mxcli --help                       > root.txt

for c in \
  version changelog \
  init add-tool \
  show list describe search syntax \
  check diff diff-local \
  callers callees refs impact structure context \
  lint report graph-report \
  exec fmt rename \
  catalog auth brain bson constant debug docker eval fix git layout log \
  marketplace mcp new playwright project-tree run serve setup skill sql \
  sync-java-deps test theme tui tunnel-hub widget extract-templates lsp diag
do
  mxcli "$c" --help > "${c}.txt" 2>&1 || echo "FAIL: $c" >> errors.txt
done

# Subcommands
mxcli auth login --help           > auth-login.txt
mxcli auth hub login --help       > auth-hub-login.txt
mxcli brain init --help           > brain-init.txt
mxcli brain capture --help        > brain-capture.txt
mxcli brain show --help           > brain-show.txt
mxcli bson dump --help            > bson-dump.txt
mxcli bson discover --help        > bson-discover.txt
mxcli catalog search --help       > catalog-search.txt
mxcli catalog show --help         > catalog-show.txt
mxcli constant set --help         > constant-set.txt
mxcli debug status --help         > debug-status.txt
mxcli docker check --help         > docker-check.txt
mxcli docker build --help         > docker-build.txt
mxcli docker run --help           > docker-run.txt
mxcli eval check --help           > eval-check.txt
mxcli eval run --help             > eval-run.txt
mxcli fix hashes --help           > fix-hashes.txt
mxcli fix property-sets --help    > fix-property-sets.txt
mxcli git note --help             > git-note.txt
mxcli layout flows --help         > layout-flows.txt
mxcli log list --help             > log-list.txt
mxcli marketplace install --help  > marketplace-install.txt
mxcli marketplace update --help   > marketplace-update.txt
mxcli marketplace diff --help     > marketplace-diff.txt
mxcli mcp capabilities --help     > mcp-capabilities.txt
mxcli playwright check --help     > playwright-check.txt
mxcli run status --help           > run-status.txt
mxcli setup mxbuild --help        > setup-mxbuild.txt
mxcli setup mxcli --help          > setup-mxcli.txt
mxcli skill list --help           > skill-list.txt
mxcli theme list --help           > theme-list.txt
mxcli widget list --help          > widget-list.txt
```

After the above runs, update `docs/research/mxcli-inventory.md`:

- Confirm each priority command's `--help` matches the inventory's Short
  description and flag list.
- Flip any row that was `verified: false` only because of source-tree ambiguity
  (not source behaviour) to `verified: true`.
- Record the installed binary's exact version (`mxcli version`) and the host OS
  at the top of this README.

Do NOT edit `.research/mxcli-v0.26.0/` to adjust these captures — that tree is
read-only reference material and is gitignored.
