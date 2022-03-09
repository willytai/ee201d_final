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
   The number of paths that has a longer arrival time than the clock cycle will be printed like so:

   -------------------------------------------------------------------------------------------------------------------------
   f2b
      1 or more signals that pass through TSV: tinst26 has negative setup slack: 5.00(required) - 6.17(arrival) = -1.17 (ns)
      1 or more signals that pass through TSV: tinst27 has negative setup slack: 5.00(required) - 6.12(arrival) = -1.12 (ns)
      .
      .
      .
      .
      1 or more signals that pass through TSV: tinst28 has negative setup slack: 5.00(required) - 6.21(arrival) = -1.21 (ns)
      1 or more signals that pass through TSV: tinst29 has negative setup slack: 5.00(required) - 6.21(arrival) = -1.21 (ns)
      1 or more signals that pass through TSV: tinst3 has negative setup slack: 5.00(required) - 6.35(arrival) = -1.35 (ns)
      1 or more signals that pass through TSV: tinst30 has negative setup slack: 5.00(required) - 6.03(arrival) = -1.03 (ns)
      1 or more signals that pass through TSV: tinst31 has negative setup slack: 5.00(required) - 6.14(arrival) = -1.14 (ns)
      1 or more signals that pass through TSV: tinst4 has negative setup slack: 5.00(required) - 6.26(arrival) = -1.26 (ns)
      1 or more signals that pass through TSV: tinst5 has negative setup slack: 5.00(required) - 6.32(arrival) = -1.32 (ns)
      1 or more signals that pass through TSV: tinst6 has negative setup slack: 5.00(required) - 6.27(arrival) = -1.27 (ns)
      1 or more signals that pass through TSV: tinst7 has negative setup slack: 5.00(required) - 6.17(arrival) = -1.17 (ns)
      1 or more signals that pass through TSV: tinst8 has negative setup slack: 5.00(required) - 6.06(arrival) = -1.06 (ns)
      1 or more signals that pass through TSV: tinst9 has negative setup slack: 5.00(required) - 6.10(arrival) = -1.10 (ns)
   64 paths greater than clock cycle
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
