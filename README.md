# 3D-Memory-Simulator

This is a high level functional simulator to evaluate the performance 3D memories. The simulator is built on the model described in [1]. It accepts a trace of memory requests as input and outputs the retrieval time from memory. Each memory request in the trace contains the address of the block to be retrieved. The memory controller in the simulator is based on FCFRFS policy and performs reordering among
requests in a window to optimize the memory access time. Since the vaults can be accessed in parallel, there is no access
overhead for elements in different vaults, i.e., t vault = 0ns. Here, it is assumed that switching the data from different vaults
across the links of 3D memory is carried out later and the overall bandwidth is determined by the access time of vaults. 

Architecture parameters of the simulator are:

• v : number of vaults in 3D memory

• l : number of layers per vault

• b : number of banks per layer in a vault

• r : number of rows in a bank

• c : number of columns in a row of a bank

Timing parameters of the simulator are:

• t_vault : time between accesses to different vaults

• t_layer : time between accesses to different layers in a vault

• t_bank : time between accesses to different banks in a layer in the same vault

• t_row : time between accesses to different rows in a bank

• t_col : time between accesses to different columns in a row


The simulator is built hierarchically. Each vault has a memory controller with 2 buffers: request and response buffers. Requests to same
bank limited by t_bank and t_col. Requests are sorted based on the fastes retrieval time.  Sorting is equivalent to reordering and is limited to the request window. Retrieval times of banks in a layer are sorted and banks on a layer can be activated simultaneously but the data can be retrieved after t_bank time. Similarly, retrieval times of different layers are sorted and the data from different layers are interleaved using t_layer. Finally, data from different vaults are sorted and interleaved with time difference of t_vault. The vault with the latest retrieval time is the total access time for a trace of requests.

Our simulator does not differentiate between reads and writes. We do not target cycle accurate performance, instead we are looking for higher order performance estimate.

Features supported:

 inter layer pipelining

 parallel vault access

 memory controller with FCFRFS

 variable architecture parameters

Development environment: Python

Configuration parameters as input and Execution time as output

Input parameters: trace of requests parameters: timing and architecture

Output: time to retrieve each of elements in the trace. Total retrieval time for the complete trace. 
