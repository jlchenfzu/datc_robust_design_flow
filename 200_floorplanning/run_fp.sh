#!/bin/bash

if test "$#" -ne 7; then
    echo "Usage: ./run_new_fp.sh <bench> <netlist> <lef> <m1_layer> <m2_layer> <clock_port> <utilization>"
    exit
fi

bench=${1}
netlist=${2}
lef=${3}
m1_layer=${4}
m2_layer=${5}
clock_port=${6}
utilization=${7}

echo "Netlist: ${netlist}"
echo "--------------------------------------------------------------------------------"
cmd="python3 ../utils/200_generate_bookshelf.py -i ${netlist}"
cmd="$cmd --lef $lef --m1_layer ${m1_layer} --m2_layer ${m2_layer} --clock ${clock_port} --util $utilization"
cmd="$cmd -o ${bench}"

echo $cmd; 
$cmd | tee ${bench}.fp.log.txt
echo ""


#echo "Restore terminal location"
#python3 merge_pl.py --nodes ${out_dir}/${base_name}.nodes --src ${out_dir}/${base_name}.pl	\
#                    --ref ${ref_bookshelf_path}/bookshelf-${bench}/${bench}.pl
#
#echo "Restore scl"
#cp ${ref_bookshelf_path}/bookshelf-${bench}/${bench}.scl ${out_dir}/${base_name}.scl
