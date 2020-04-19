#!/usr/bin/bash
# Pulled from https://stackoverflow.com/questions/18641864/git-bash-shell-fails-to-create-symbolic-links
# https://stackoverflow.com/users/124119/camilo-martin

# Detect windows (assumes we are in 'msysgit' or similar).
windows() { [[ -n "$WINDIR" ]]; }

# Cross-platform symlink function.
#  With one parameter, it will check whether the parameter is a symlink.
#  With two parameters, it will create a symlink to a file or directory,
#   with syntax: link $linkname $target
if [[ -z "$2" ]]; then
    # Link-checking mode.
    if windows; then
        fsutil reparsepoint query "$1" > /dev/null
    else
        [[ -h "$1" ]]
    fi
else
    # Link-creation mode.
    if windows; then
        # Windows needs to be told if it's a directory or not. Infer that.
        # Also: note that we convert `/` to `\`. In this case it's necessary.
        if [[ -d "$2" ]]; then
            cmd <<< "mklink /D \"$1\" \"${2//\//\\}\"" > /dev/null
        else
            cmd <<< "mklink \"$1\" \"${2//\//\\}\"" > /dev/null
        fi
    else
        # You know what? I think ln's parameters are backwards.
        ln -s "$2" "$1"
    fi
fi
