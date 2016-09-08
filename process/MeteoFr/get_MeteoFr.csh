#!/bin/csh
###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date$
# $Revision$
# $Author$
# $Id$
###############################################################

set center = "MeteoFr"
set norm = "moist"
set bdate = "2014120100"
set edate = "2015030100"
set remote_datadir = "MOIST/WINTER"
set datadir = "$data/FSOI/data/$center"

# Load the FTP information from MeteoFr.txt
source MeteoFr.netrc

set adate = $bdate
while ( $adate < $edate )

    set yyyy = `echo $adate | cut -c1-4`
    set mm   = `echo $adate | cut -c5-6`
    set dd   = `echo $adate | cut -c7-8`
    set hh   = `echo $adate | cut -c9-10`

    mkdir -p $datadir/$norm/$yyyy$mm$dd$hh
    cd       $datadir/$norm/$yyyy$mm$dd$hh

    echo "Fetching files for ... $norm, $adate"

    ftp -in $ftphost << EOT
user $ftpuser $ftppasswd
binary
cd $remote_datadir/$yyyy$mm$dd$hh
mget *.tar.gz
bye
EOT

    @ nfiles = `ls -1 *.tar.gz | wc -l`
    echo "Fetched  files for ... $norm, $adate = $nfiles"

    foreach tarball ( `ls -1 *.tar.gz` )
        tar -xzvf $tarball
    end

    set adate = `advance_time $adate +6h`

end

exit 0
