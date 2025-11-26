#!/bin/bash
set -e

git pull

# Make sure we have submodules initialized
git submodule init 

git submodule update --remote --recursive


# For each submodule in .gitmodules
git config -f .gitmodules --get-regexp submodule\..*\.path | while read -r key path; do
    # Get submodule name from key
    name=$(echo $key | sed 's/submodule\.\(.*\)\.path/\1/')
    # Get branch from .gitmodules
    branch=$(git config -f .gitmodules submodule.$name.branch || echo "master")

    echo "==> Processing submodule $name at $path (branch $branch)"

    # Ensure local config tracks the branch
    git config submodule.$path.branch $branch

    # Update and init the submodule
    git submodule update --init --remote $path

    # Enter the submodule and force checkout branch
    (
        cd $path
        git fetch origin $branch
        git checkout $branch || git checkout -b $branch origin/$branch
        git pull origin $branch
    )
done
