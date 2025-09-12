#!/bin/bash
# remove_submodules.sh
# Usage: ./remove_submodules.sh submodule_path1 submodule_path2 ...

if [ $# -eq 0 ]; then
    echo "Usage: $0 <submodule_path> [<submodule_path> ...]"
    exit 1
fi

for submodule in "$@"; do
    echo ">>> Removing submodule: $submodule"

    # Step 1. Deinit if still tracked
    git submodule deinit -f -- "$submodule" || true

    # Step 2. Remove from index
    git rm -f --cached "$submodule" || true

    # Step 3. Delete leftover .git/modules data
    rm -rf ".git/modules/$submodule"

    # Step 4. Delete working directory
    rm -rf "$submodule"

    echo ">>> Done: $submodule"
    echo
done

echo "✅ All requested submodules have been removed."
