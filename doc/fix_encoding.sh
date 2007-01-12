#!/bin/sh

sed -i \
    's/<?xml version="1.0" encoding="iso-8859-1"?>//' \
    $@
    
sed -i \
    's/<?xml version="1.0" encoding="ascii"?>//' \
    $@
