#!/bin/sh

if [ -z "$1" ];
then
	echo Please specify year as argument
	exit 1
fi

if [ -z `echo $1|grep -E "^[0-9]{4}$"` ];
then
	echo Please specify year as 4 digits
	exit 1
fi

YEAR=$1

SEARCH_RE="Copyright 2018-[0-9]{4} Fetch.AI Limited"
UPDATE_STR="Copyright 2018-${YEAR} Fetch.AI Limited"

echo $UPDATE_STR


for i in `grep -l -E -R "${SEARCH_RE}" --include "*.py" ../`;
do
	sed -E -e "s/${SEARCH_RE}/${UPDATE_STR}/" -i $i
	echo Updated: $i
done 