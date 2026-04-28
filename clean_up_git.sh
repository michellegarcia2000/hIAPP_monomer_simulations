#!bin/bash

find . -size +100M -not -path './.git/*' | sed 's|^\./||' >> .gitignore && sort -u .gitignore -o .gitignore
