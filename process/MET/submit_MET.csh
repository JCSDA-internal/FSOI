#!/bin/csh
###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date$
# $Revision$
# $Author$
# $Id$
###############################################################

set center = "MET"
set dir_scripts = "$data/FSOI/process/$center"
set indir = "$data/FSOI/data/$center"
set outdir = "$data/FSOI/ascii/$center"
set bdate = "2014120100"
set edate = "2015030100"
set norm = "dry"

cd $dir_scripts

set adate = $bdate
while ( $adate < $edate )

    echo "Creating job script for $adate"

    rm -f job_script.csh
cat > job_script.csh << EOF
#!/bin/csh
#SBATCH --job-name=$center.$norm.$adate
#SBATCH --account=star
#SBATCH --partition=serial
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:30:00
#SBATCH --output=/scratch/%u/output/$center/log.$norm.$adate.%j

source /etc/csh.cshrc

echo "Job started at \`date\`"

set yyyymmdd = \`echo $adate | cut -c1-8\`
set hh = \`echo $adate | cut -c9-10\`

set input = $indir/\${yyyymmdd}T\${hh}00Z.FSO
set output = $outdir/$center.$norm.$adate.txt

if ( ! -e \$input ) then
    echo "ERROR: \$input does not exist, nothing to process, EXITING"
    echo "Job ended at \`date\`"
    exit 0
endif

cd $dir_scripts
./process_$center.py -i \$input -o \$output

echo "Job ended at \`date\`"
exit 0
EOF
    chmod +x job_script.csh

    sbatch job_script.csh

    set adate = `advance_time $adate +6h`
end

rm -f job_script.csh

exit 0
