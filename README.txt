# EE201D Final Project
  Wei-Chen Tai, 105493001

## Environment Setup

  1. Change to C Shell  
     $ csh

  2. Move `main.sh` to the `project/` directory (the directory that contains `scripts_own/`)
     $ mv main.sh ../


## Run
  1. Enter the `project/` directory
     $ cd ..

  2. Run `main.sh` with the following two arguments
     - design: t1, t2, t3, t4
     - constraint: 1, 2

     For example, to run the first test case:
     $ ./main.sh t1 1

  3. The program will show some information regarding the three different approaches and calculate the yield:

     --------------------------Yield--------------------------
     => SoC yield: 0.999874
     => F2B yield: 0.938271
     => F2F yield: 0.947723
     => The flow with the highest estimated yield is: soc (yield=0.9998738409187263)
     => Choose a flow to continue [soc/f2b/f2f] (hit enter for default: soc):

  4. Follow the prompt and enter the desired flow (case insensitive), the default is always the flow with the highest yield.
     The program times out after approximately 10 seconds if no option is chosen and selects the default flow.
     When finished, the location of the results will be shown like so:

     *************************************************************
     * Innovus script finished
     *
     * Results:
     * --------
     * Layout:  soc_output/riscv_soc_io.gds
     * Netlist: soc_output/riscv_soc_io_postrouting.v
     * Timing:  soc_output/riscv_soc_io_postrouting_setup.tarpt
     * DRC:     soc_output/riscv_soc_io.drc.rpt
     * Design:  soc_output/design.invs
     *
     * Type 'exit' to quit
     *
     *************************************************************

     the program will exit itself, there is no need to type anything at this point.


## Timing Checker
   For the 3D flow (F2B/F2F), there will be additional timing closure check after the physical design flow is finished.
   The information of the path that the signal travels will be printed to the console. Some signals travel from the bottom
   die to the top die, and some from the top die to the bottom die. The nets that they pass will be printed in order. The
   output is like so:

   -------------------------------------------------------------------------------------------------------------------------
   f2f
       The signal that passes through TSV: tbus_read_data31, has arrival time: 4.48 (ns), which is smaller than clock cycle: 5.00 (ns) (MET)
           -------- nets --------
           - clock_int (starting net, top)
           - bus_read_data_int[31]
           - FE_OFN235_bus_read_data_int_31
           - bus_read_data[31] (signal crossing 'tbus_read_data31' from top die to bottom die)
           - bus_read_data_int[31]
           - n_844
           - n_20088
           - n_4178
           - n_4923
           - n_526
           - n_5562
           - n_5635
           - n_5708 (terminal net, bottom)
           ----------------------
         .
         .
         .
        The signal that passes through TSV: tpc1, has arrival time: 0.86 (ns), which is smaller than clock cycle: 5.00 (ns) (MET)
            -------- nets --------
            - clock_int (starting net, bottom)
            - pc_int[1]
            - FE_OFN109_pc_int_1
            - pc[1] (signal crossing 'tpc1' from bottom die to top die)
            - pc_int[1]
            - FE_OFN164_pc_int_1 (terminal net, top)
            ----------------------
         .
         .
         .
        The signal that passes through TSV: tpc9, has arrival time: 2.18 (ns), which is smaller than clock cycle: 5.00 (ns) (MET)
            -------- nets --------
            - clock_int (starting net, bottom)
            - pc_int[9]
            - FE_OFN89_pc_int_9
            - FE_OFN90_pc_int_9
            - pc[9] (terminal net, bottom)
            - connection failed on the bottom die, estimating arrival time of cross-die signal by doubling the value
         .
         .
         .
        The signal that passes through TSV: tinst8, has arrival time: 6.36 (ns), which is greater than clock cycle: 5.00 (ns) (NOT MET)
            -------- nets --------
            - clock_int (starting net, top)
            - inst_int[8]
            - FE_OFN315_inst_int_8
            - inst[8] (terminal net, top)
            - connection failed on the top die, estimating arrival time of cross-die signal by doubling the value
            ----------------------
         .
         .
         .
   1 paths greater than clock cycle
   -------------------------------------------------------------------------------------------------------------------------


## Other Testcases
  |----|---------------|------------|-------|------------------|
  |    | Compute Power | SRAM Power | Pitch | Command          |
  |----|---------------|------------|-------|------------------|
  | T1 | Nominal       | Nominal    | Large | $ ./main.sh t1 1 |
  | T2 | 10x           | Nominal    | Large | $ ./main.sh t2 1 |
  | T3 | Nominal       | 10x        | Large | $ ./main.sh t3 1 |
  | T4 | 10x           | 10x        | Large | $ ./main.sh t4 1 |
  | T5 | Nominal       | Nominal    | Small | $ ./main.sh t1 2 |
  | T6 | 10x           | Nominal    | Small | $ ./main.sh t2 2 |
  | T7 | Nominal       | 10x        | Small | $ ./main.sh t3 2 |
  | T8 | 10x           | 10x        | Small | $ ./main.sh t4 2 |
  |----|---------------|------------|-------|------------------|
