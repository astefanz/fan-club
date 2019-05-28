#!/bin/bash

# NOTE: chmod 755 will give you read, write and execute permission.
# Everyone else gts only read and execute permission

target_dir="./"
source_dir=~/Desktop/thermalpro_ctg_19-20/

target_file=CTG19.?000[123]
#target_file=CTG20.?000[89]

#echo "getting: " $source_dir$target_file $target_dir
mv $source_dir$target_file $target_dir
ls

