# Setup design config
set netlist {netlist/riscv_soc_io.sv}
set top_cell riscv_soc_io
set sdc {netlist/riscv_soc_io.sdc}
# Modify those paths to reflect your directory setup
set libdir "/w/class.1/ee/ee201o/ee201ota/ee201d/project/lib"
set lefdir "/w/class.1/ee/ee201o/ee201ota/ee201d/project/lef"
set nanlef "/w/class.1/ee/ee201o/ee201ota/ee201d/NangateOpenCellLibrary_PDKv1_3_v2010_12/Back_End/lef"
set nanlib "/w/class.1/ee/ee201o/ee201ota/ee201d/NangateOpenCellLibrary_PDKv1_3_v2010_12/Front_End/Liberty/CCS"
set lef [list $nanlef/NangateOpenCellLibrary.tech.lef $nanlef/NangateOpenCellLibrary.macro.lef $lefdir/sram_32_256_freepdk45.lef $lefdir/bump.lef $lefdir/IOCELLBUFANTENNAIN_PAD.lef $lefdir/IOCELLBUFANTENNAOUT_PAD.lef]
# others
set DNAME riscv_soc_io
set OUTPUTDIR soc_output
file mkdir $OUTPUTDIR
