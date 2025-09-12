#!/bin/bash
# remove_submodules.sh
# Usage: ./remove_submodules.sh submodule_path1 submodule_path2 ...

if [ $# -eq 0 ]; then
    echo "Usage: $0 <submodule_path> [<submodule_path> ...]"
    exit 1
fi

for submodule in "$@"; do
    echo ">>> Removing submodule: $submodule"

    # Normalize: full path + basename
    base_name=$(basename "$submodule")

    # Step 1. Deinit if still tracked
    git submodule deinit -f -- "$submodule" || true

    # Step 2. Remove from index
    git rm -f --cached "$submodule" || true

    # Step 3. Remove leftover config entries
    git config --remove-section "submodule.$submodule" 2>/dev/null || true
    git config --remove-section "submodule.$base_name" 2>/dev/null || true

    # Step 4. Delete leftover .git/modules data (both possibilities)
    rm -rf ".git/modules/$submodule"
    rm -rf ".git/modules/$base_name"

    # Step 5. Delete working directory
    rm -rf "$submodule"

    # Step 6. Remove from .gitmodules if present
    if grep -q "$submodule" .gitmodules 2>/dev/null; then
        echo ">>> Cleaning .gitmodules entry"
        git config -f .gitmodules --remove-section "submodule.$submodule" 2>/dev/null || true
    fi

    echo ">>> Done: $submodule"
    echo
done

echo "✅ All requested submodules have been removed."
echo "👉 Don’t forget to commit the changes:"
echo "   git add .gitmodules"
echo "   git commit -m 'Remove submodules'"
