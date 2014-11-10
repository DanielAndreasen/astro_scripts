#!/bin/bash


## Add a '#' in the beginning of every line which contains 'center'
##
## Caution: Has to remove dates manually!
##
## For more details look here:
## http://stackoverflow.com/questions/19979653/add-a-to-every-line-in-a-file-with-certain-string-with-sed


FILE=$1

sed -i '/center/s/^\([^#]\)/#\1/' $FILE
