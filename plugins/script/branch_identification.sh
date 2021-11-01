#!/bin/bash

# TODO: Provide name of python files. There are two limitations of this script 1) only search at root directory 2) does not recursively search 
DIR="app CondDBFW"

OUTPUT_FILE=$(pwd)/perfci/plugins/script/conditionals_info


## Create a tmp with timestamp file if it exists
# if test -f "$OUTPUT_FILE"; then
#     mv $OUTPUT_FILE $OUTPUT_FILE$(date +%s)
# fi

# Read file based on the path supplied. 
for dir in $DIR ;
do
    #only_dir=`$(pwd)/perfci/plugins/script/readlink.sh $dir`
    only_dir=`readlink -f $dir`
    filenames+=`ls $only_dir/*.py`
    filenames+=" "
    
done

# file1="/Users/omarjaved/Documents/Omar/Projects/CERN/cianalytics/main.py"

# Search for conditionals. In python we have if, else, and elif.
# Three while loops for identifying if blocks, else and elif blocks separately


for file in $filenames;
do
    
    while IFS='' read -r line ; do
        if [[ $line == *"#"* ]]; then
            continue
        fi
        file_info=$file #$( echo "$line" | cut -d":" -f1 )
        line_num=$( echo "$line" | cut -d":" -f1 )  
        echo $file_info:$line_num, "if" >> $OUTPUT_FILE
        #echo $comma_sep
    done < <(grep -REn '\bif\b' $file)

    while IFS='' read -r line ; do
        if [[ $line == *"#"* ]]; then
            continue
        fi
        file_name=$file #$(echo "$line" | cut -d':' -f1 ) 
        line_num=$(echo "$line" | cut -d':' -f1 )
        line_num=$((line_num+1))
        echo $file_name:$line_num, "else" >> $OUTPUT_FILE
    done < <(grep -REn 'else:' $file)

     while IFS='' read -r line ; do
        if [[ $line == *"#"* ]]; then
            continue
        fi
        file_info=$file #$( echo "$line" | cut -d":" -f1 )
        line_num=$( echo "$line" | cut -d":" -f1 )  
        echo $file_info:$line_num, "elif" >> $OUTPUT_FILE
        #echo $comma_sep
    done < <(grep -REn '\belif\b' $file)

    while IFS='' read -r line ; do
        if [[ $line == *"#"* ]]; then
            continue 
        fi

        file_info=$file #$( echo "$line" | cut -d":" -f1 )
        line_num=$( echo "$line" | cut -d":" -f1 )  
        echo $file_info:$line_num, "for" >> $OUTPUT_FILE
        #echo $comma_sep
    done < <(grep -REn 'for.*:' $file)

done    
