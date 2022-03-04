# Setup design config
set netlist {netlist/riscv_soc_io.sv}
set top_cell riscv_soc_io
set sdc {netlist/riscv_soc_io.sdc}
# Modify those paths to reflect your directory setup
set libdir "/w/classproj/ee201d/weichen/project/lib"
set lefdir "/w/classproj/ee201d/weichen/project/lef"
set lef [list $lefdir/NangateOpenCellLibrary.tech.lef $lefdir/NangateOpenCellLibrary.macro.lef $lefdir/sram_32_256_freepdk45.lef $lefdir/bump.lef $lefdir/IOCELLBUFANTENNAIN_PAD.lef $lefdir/IOCELLBUFANTENNAOUT_PAD.lef]
# others
set DNAME riscv_soc_io
set OUTPUTDIR soc_output
file mkdir $OUTPUTDIR
