#!/bin/bash

## Small script that prepare VALD linelist
## to read in python
##
## USAGE:
##  ./VALDprepare.sh <filename>.gz <output>
##
## NOTES:
##  <output> is optional and should be without extensions
##
## OUTPUT:
##  Return two files: Data file ready for Python to read
##  and a file with the references at the end of the original
##  VALD file, .dat and .ref respectively

FILE=$1
OUTPUT=$2


# Get the filename without extension
filename=`basename $FILE .gz`


if [ $OUTPUT ]
then
    filename=$OUTPUT
fi


# Unpack the file to <filename>
gunzip -c $FILE > $filename


# Add '#' to the first two lines (header)
sed '1,2{/^#/!s/^/#/}' $filename > $filename.tmp
rm -f $filename

# Remove all ' in file
sed "s/[']//g" $filename.tmp > $filename.tmp1
rm -f $filename.tmp

# Remove the references
sed -n '/ References:/q;p' $filename.tmp1 > $filename.dat

# Put the references in a seperate file and delete others
diff $filename.dat $filename.tmp1 > $filename.tmp
tail -n +2 "$filename.tmp" > $filename.ref

rm -f $filename.tmp1 $filename.tmp

printf "\nCreated two files:\n"
printf "\t- $filename.dat -- The data file\n"
printf "\t- $filename.ref -- The references\n"
