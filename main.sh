# setup environment for innovus
setenv CDSHOME /w/apps3/Cadence/IC617
source /w/apps3/Cadence/IC617/SETUP
source /w/apps3/Cadence/ASSURA415-617/SETUP
source /w/apps3/Cadence/SPECTRE161/SETUP
source /w/apps3/Cadence/EXT171/SETUP

python3 scripts_own/main.py \
        --soc netlist/riscv_soc_io_${1}.rep \
        --f2b-top netlist/riscv_top_f2b_io_${1}.rep \
        --f2b-bot netlist/riscv_bottom_f2b_io_${1}.rep \
        --f2b-bot-netlist netlist/riscv_bottom_f2b_io.sv \
        --f2b-top-netlist netlist/riscv_top_f2b_io.sv \
        --f2f-top netlist/riscv_top_f2f_io_${1}.rep \
        --f2f-bot netlist/riscv_bottom_f2f_io_${1}.rep \
        --f2f-bot-netlist netlist/riscv_bottom_f2f_io.sv \
        --f2f-top-netlist netlist/riscv_top_f2f_io.sv \
        --tech-const tech/tech_const_${2}.txt \
        --script-dir scripts_own/
