# Setup design config
set netlist {netlist/riscv_top_f2f_io.sv}
set top_cell riscv_top_f2f_io
set sdc {netlist/riscv_top_f2f_io.sdc}
# Modify those paths to reflect your directory setup
set libdir "/w/classproj/ee201d/weichen/project/lib"
set lefdir "/w/classproj/ee201d/weichen/project/lef"
set lef [list $lefdir/NangateOpenCellLibrary.tech.lef $lefdir/NangateOpenCellLibrary.macro.lef $lefdir/sram_32_256_freepdk45.lef $lefdir/bump.lef $lefdir/IOCELLBUFANTENNAIN_PAD.lef $lefdir/IOCELLBUFANTENNAOUT_PAD.lef $lefdir/TSV.lef]
set DNAME riscv_core_io
set OUTPUTDIR output



## comment these out later
# Initialize design
suppressMessage TECHLIB-436
suppressMessage IMPVL-159
set init_import_mode {-treatUndefinedCellAsBbox 0 -keepEmptyModule 1 }
set init_verilog $netlist
set init_design_netlisttype "Verilog"
set init_design_settop 1
set init_top_cell $top_cell
set init_lef_file $lef
set init_pwr_net VDD
set init_gnd_net VSS

# MCMM setup
create_constraint_mode -name CON -sdc_file [list $sdc]
create_library_set -name WC_LIB_SLOW -timing [list $libdir/NangateOpenCellLibrary_slow_ccs.lib $libdir/sram_32_256_freepdk45_SS_1p0V_25C.lib $libdir/IOCELLBUFANTENNAIN_ss.lib $libdir/IOCELLBUFANTENNAOUT_ss.lib $libdir/tsv.lib]
create_rc_corner -name _slow_rc_corner_ -T 125
create_delay_corner -name WC_SLOW -library_set WC_LIB_SLOW -rc_corner _slow_rc_corner_
create_analysis_view -name WC_SLOW_VIEW -delay_corner WC_SLOW -constraint_mode CON

create_library_set -name WC_LIB_FAST -timing [list $libdir/NangateOpenCellLibrary_fast_ccs.lib $libdir/sram_32_256_freepdk45_FF_1p0V_25C.lib $libdir/IOCELLBUFANTENNAIN_ff.lib $libdir/IOCELLBUFANTENNAOUT_ff.lib $libdir/tsv.lib]
create_rc_corner -name _fast_rc_corner_ -T -40
create_delay_corner -name WC_FAST -library_set WC_LIB_FAST -rc_corner _fast_rc_corner_
create_analysis_view -name WC_FAST_VIEW -delay_corner WC_FAST -constraint_mode CON

# Initialize design
init_design -setup {WC_SLOW_VIEW} -hold {WC_FAST_VIEW}

setAnalysisMode -analysisType onChipVariation -cppr both
setDesignMode -process 45

# Report initial setup and hold time, post-synthesis but before physical design
#report_timing -check_type setup -nworst  10 -net > ${OUTPUTDIR}/${DNAME}_init_setup.tarpt
#report_timing -early -nworst  10 -net > ${OUTPUTDIR}/${DNAME}_init_hold.tarpt

setMaxRouteLayer 7
