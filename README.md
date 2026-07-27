# PoolHelper

NOTE: There are multiple different versions of this data analysis program in each branch of this repository. 
This is because the code was initially developed on an internal git server. I uploaded this repository to act one location with which to showcase this program and its multiple variants.

Branches:
Main: Pool Helper 2.0. This is a general all-round improvement on version one of the program which was not uploaded to this repository.
Pool Finder: Web-app based data visualization tool
Pool Helper Simulation: A version of the program which uses simulations to raise warning signs of contamination in the lab.

Data analysis tool for ePCR done in 365-well plates

Regarding the code:
This program was designed to run within the laboratory environment in which it was developed and usually needs a connection to the lab's LIMS database to function properly.
This version has been modified slightly to allow it to run on a local machine without a LIMS connection. To do so, you must first run the main.py script. Then, in the terminal, type "OFFLINE", then "Y", then "rf", then "1" and an example output file will be generated in the Output directory.
