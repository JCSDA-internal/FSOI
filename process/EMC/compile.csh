#!/bin/csh -x
###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date$
# $Revision$
# $Author$
# $Id$
###############################################################

set todo = $1
set center = "emc"

if ( $todo == "clean" ) then
    rm -f $center.pyf $center.so read_$center.x $center.mod $center.o read_$center.o
else if ( $todo == "build" ) then
    rm -f $center.pyf $center.so $center.mod
    f2py -m $center -h $center.pyf $center.f90
    f2py -c --fcompiler=gnu95 $center.pyf $center.f90
else if ( $todo == "test" ) then
    rm -f read_$center.x $center.mod $center.o read_$center.o
    set FC = "gfortran"
    set FFLAGS = "-g -C -traceback"
    $FC -c $FFLAGS $center.f90
    $FC -c $FFLAGS read_$center.f90
    $FC $FFLAGS -o read_$center.x *.o
else
    echo "undefined task: $todo"
endif
