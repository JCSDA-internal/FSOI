#!/bin/csh
###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date$
# $Revision$
# $Author$
# $Id$
###############################################################

set todo = $1

set echo

if ( $todo == 'clean' ) then
    rm -f emc.pyf emc.so read_emc.x emc.mod emc.o read_emc.o
else if ( $todo == 'build' ) then
    rm -f emc.pyf emc.so emc.mod
    f2py -m emc -h emc.pyf emc.f90
    echo "open emc.pyf and edit the len=20, len=20 to *20,*20 in the intent out section of get_data"
    vi emc.pyf
    f2py -c --fcompiler=intelem emc.pyf emc.f90
else if ( $todo == 'test' ) then
    rm -f read_emc.x emc.mod emc.o read_emc.o
    set FC = "ifort"
    set FFLAGS = "-g -C -traceback"
    $FC -c $FFLAGS emc.f90
    $FC -c $FFLAGS read_emc.f90
    $FC $FFLAGS -o read_emc.x *.o
else
    echo "undefined task: $todo"
endif
