source "scripts_own/init_3d_f2b_top.tcl"

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
report_timing -check_type setup -nworst  10 -net > ${OUTPUTDIR}/${DNAME}_init_setup.tarpt
report_timing -early -nworst  10 -net > ${OUTPUTDIR}/${DNAME}_init_hold.tarpt

setMaxRouteLayer 7

source "scripts_own/fp_3d_f2b_top.tcl"

# Define global power nets
globalNetConnect VSS -type pgpin -all -pin VSS
globalNetConnect VDD -type pgpin -all -pin VDD

# Create power structures. DON'T CHANGE addRing statement.
addRing -layer {top metal5 bottom metal5 left metal6 right metal6} -spacing {top 1.5 bottom 1.5 left 1.5 right 1.5} -width {top 2 bottom 2 left 2 right 2} -center 1 -nets { VDD VSS } -type core_rings -follow io
addStripe -nets {VSS VDD} -layer metal6 -direction vertical -width 2 -spacing 1.5 -set_to_set_distance 40 -start_from left -start_offset 40 -switch_layer_over_obs false -max_same_layer_jog_length 2 -padcore_ring_top_layer_limit metal10 -padcore_ring_bottom_layer_limit metal1 -block_ring_top_layer_limit metal10 -block_ring_bottom_layer_limit metal1 -use_wire_group 0 -snap_wire_center_to_grid None

#setSrouteMode -viaConnectToShape { noshape }
sroute -connect { blockPin padPin corePin floatingStripe } -layerChangeRange { metal1(1) metal10(10) } -blockPinTarget { nearestTarget } -padPinPortConnect { allPort oneGeom } -padPinTarget { nearestTarget } -corePinTarget { firstAfterRowEnd } -floatingStripeTarget { blockring padring ring stripe ringpin blockpin followpin } -allowJogging 1 -crossoverViaLayerRange { metal1(1) metal10(10) } -nets { VDD VSS } -allowLayerChange 1 -blockPin useLef -targetViaLayerRange { metal1(1) metal10(10) }

report_power -outfile ${OUTPUTDIR}/${DNAME}_beforePlace.parpt

# Place standard cells - timing-driven by default
# Enable placement of IO pins as well
setPlaceMode -place_global_place_io_pins true -reorderScan false
placeDesign
place_opt_design

# Legalize placement if necessary 
refinePlace
report_power -outfile ${OUTPUTDIR}/${DNAME}_afterPlace.parpt

# Save Verilog netlist post-placement
saveNetlist -excludeLeafCell ${OUTPUTDIR}/${DNAME}_placed.v

# Optimize for setup time before clock tree synthesis (CTS)
optDesign -preCTS

# Perform trial route and get initial timing results
trialroute

# Build static timing model for the design
buildTimingGraph

# Run clock tree synthesis (CTS)
set_ccopt_property buffer_cells {BUF_X1 BUF_X2} 
set_ccopt_property inverter_cells {INV_X1 INV_X2 INV_X4 INV_X8 INV_X16}
#set_ccopt_property sink_type stop -pin tclock/in
#set_ccopt_property -pin tclock/in -delay_corner WC_SLOW capacitance_override 0.05
#set_ccopt_property -pin tclock/in -delay_corner WC_FAST capacitance_override 0.05
create_ccopt_clock_tree_spec
ccopt_design -cts

# Refine placement again
refinePlace 

# More trial routing post-CTS to get better estimates
setTrialRouteMode -highEffort true
trialRoute

# Extract RC delay estimates
setExtractRCMode -layerIndependent 1
extractRC

# Report clock tree synthesis results
report_ccopt_clock_trees -file ${OUTPUTDIR}/postcts.ctsrpt
report_ccopt_skew_groups -local_skew -file ${OUTPUTDIR}/postcts_localskew.ctsrpt

# Run post-CTS timing analysis
setAnalysisMode -checkType hold -asyncChecks async -skew true
buildTimingGraph
report_timing -nworst 10 -net > ${OUTPUTDIR}/${DNAME}_postcts_hold.tarpt

# Optimize for hold time after CTS
optDesign -postCTS -hold 

# Perform post-CTS RC extraction
setExtractRCMode -engine preRoute -assumeMetFill
extractRC

# Run timing analysis again
buildTimingGraph
report_timing -nworst 10 -net > ${OUTPUTDIR}/${DNAME}_prerouting.tarpt

# Connect all new cells to VDD/GND
globalNetConnect VDD -type tiehi
globalNetConnect VDD -type pgpin -pin VDD -override

globalNetConnect VSS -type tielo
globalNetConnect VSS -type pgpin -pin VSS -override

# Run global and detailed routing
globalDetailRoute

# Optimize post routing
optDesign -hold -postRoute

# Extract RC delays
setExtractRCMode -engine postRoute
extractRC

# Report timing
buildTimingGraph
report_timing -nworst 10 -net > ${OUTPUTDIR}/${DNAME}_postrouting_hold.tarpt

# Report setup time
setAnalysisMode -checkType setup -asyncChecks async -skew true
buildTimingGraph
report_timing -nworst 10 -net > ${OUTPUTDIR}/${DNAME}_postrouting_setup.tarpt

# Add filler cells
addFiller -cell FILLCELL_X1 FILLCELL_X2 FILLCELL_X4 FILLCELL_X8 FILLCELL_X16 

verify_drc -limit 10000 -report ${OUTPUTDIR}/${DNAME}.drc.rpt

# Write the final results
#streamOut ${OUTPUTDIR}/${DNAME}.gds -libName DesignLib -structureName $DNAME -merge { ?? } -stripes 1 -units 10000 -mode ALL

defOut -floorplan -netlist -routing ${OUTPUTDIR}/${DNAME}_postrouting.def
rcOut -spef ${OUTPUTDIR}/${DNAME}_postrouting.spef


saveNetlist -excludeLeafCell ${OUTPUTDIR}/${DNAME}_postrouting.v
report_power -outfile ${OUTPUTDIR}/${DNAME}_route.parpt
summaryReport -noHtml -outfile ${OUTPUTDIR}/summary.rpt
reportGateCount -level 10 -outfile ${OUTPUTDIR}/gate_count.rpt
checkDesign -io -netlist -physicalLibrary -powerGround -tieHilo -timingLibrary -floorplan -place -noHtml -outfile ${OUTPUTDIR}/design.rpt
saveDesign ${OUTPUTDIR}/design.invs

puts "*************************************************************"
puts "* Innovus script finished"
puts "*"
puts "* Results:"
puts "* --------"
puts "* Layout:  ${OUTPUTDIR}/${DNAME}.gds"
puts "* Netlist: ${OUTPUTDIR}/${DNAME}_postrouting.v"
puts "* Timing:  ${OUTPUTDIR}/${DNAME}_postrouting_setup.tarpt"
puts "* DRC:     ${OUTPUTDIR}/${DNAME}.drc.rpt"
puts "*"
puts "* Type 'exit' to quit"
puts "*"
puts "*************************************************************"

