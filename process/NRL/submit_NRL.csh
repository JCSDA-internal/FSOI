#!/bin/csh
###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date$
# $Revision$
# $Author$
# $Id$
###############################################################

set center = "NRL"
set dir_scripts = "$data/FSOI/process/$center"
set indir = "/data/users/jxu/FSOI/FSO_data/$center/original/DJF_original"
set outdir = "/data/users/rmahajan/FSOI/ascii2/$center"
set bdate = "2014120100"
set edate = "2015030100"

cd $dir_scripts

set adate = $bdate
while ( $adate < $edate )

    echo "Creating job script for $adate"

    rm -f job_script.csh
cat > job_script.csh << EOF
#!/bin/csh
#SBATCH --job-name=$center$adate
#SBATCH --account=star
#SBATCH --partition=serial
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:30:00
#SBATCH --output=/scratch/%u/output/$center/log.$adate.%j

source /etc/csh.cshrc

echo "Job started at \`date\`"

cd $dir_scripts
./process_$center.py -i $indir -o $outdir -a $adate

echo "Job ended at \`date\`"
exit 0
EOF
    chmod +x job_script.csh

    sbatch job_script.csh

    set adate = `advance_time $adate +6h`
end

rm -f job_script.csh

exit 0
