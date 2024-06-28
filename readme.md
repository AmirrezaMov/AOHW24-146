**Team number:** AOHW-146
**Project name:** Decoding the Seizure Storm: Leveraging the ACAP Heterogeneity for Large-Scale Neural-Mass Brain Modeling
**Link to YouTube Video(s):** https://youtu.be/hnX7VlAjWaU (Some parts of the demo shown in this video is cut to meet the 2 minute budget)
**Link to project repository:** https://github.com/AmirrezaMov/AOHW24-146

**University name:** Delft University of Technology (TU Delft)
**Participant:** Amirreza Movahedin
**Email:** [A.Movahedin@student.tudelft.nl](mailto:A.Movahedin@student.tudelft.nl)
**Supervisor name:** Dr.ir.Christos Strydis
**Supervisor e-mail:** [C.Strydis@tudelft.nl](mailto:C.Strydis@tudelft.nl)

**Board used:** VCK190 (VC1902 Versal AI Core Series)
**Software Version:** 2022.2

#### Brief description of project:
In this project we implemented The Virtual Brain (TVB) style brain models on the Versal Adaptive SoC. Our system performs large-scale brain model simulations for used for addressing brain diseases, such as epilepsy. Two version of this systems are implemented: A version that only uses the AI Engines of the Versal (the AIE-Only System), and a version that uses the heterogeneity of the Versal, and utilizes both the Programmable Logic and the AI Engines (the Heterogeneous/Hybrid System).

#### Description of archive:

The top archive includes the following:
1) The AIE-Only.zip archive: The project files of the AIE-Only implementation exported from Vitis IDE
2) The Heterogeneous.zip archive: The project files of the Heterogeneous implementation exported from Vitis IDE
3) The VersalDriver Folder: Contains Python scripts used for testing the system


##### AIE-Only.zip Archive: 
This archive, contains the following folders:
* Two platform projects: **base_pfm_vck190** is the platform project for the AIE and PL, **ps_pfm_vck190** is the platform project for the Processing System
* **nmm_system project:** Contains the project folders of PL, AIE, and linking. It also contains the built files for the entire system (in Hardware and Emulation-HW folders):
    - **hw_kernels:** This is the PL project folder. The src folder contains the source code of the PL modules implemented.
    - **nmm:** This is the AIE project folder. The src folder contains the graph file (project.h) and the kernel source files (in kernels folder)
    - **nmm_system_hw_link:** This is the linking project folder. It contains connectivity file and built folders.
* **ps_app_system:** Contains the project folder for the PS application:
    - **ps_app:** This is the project folder of the PS application. It contains the libraries and the source files (src folder).

##### Heterogeneous.zip Archive:

This archive, contains the following folder:
* Two platform projects: **base_pfm_vck190** is the platform project for the AIE and PL, **ps_pfm_vck190** is the platform project for the Processing System
* **hybrid_system_system project:** Contains the project folders of PL, AIE, and linking. It also contains the built files for the entire system (in Hardware and Emulation-HW folders):
    - **hw_kernels:** This is the PL project folder. The src folder contains the source code of the PL modules implemented.
    - **hybrid_system:** This is the AIE project folder. The src folder contains the graph file (project.h) and the kernel source files (in kernels folder)
    - **hybrid_system_system_hw_link:** This is the linking project folder. It contains connectivity file and built folders.
* **ps_app_system:** Contains the project folder for the PS application:
    - **ps_app:** This is the project folder of the PS application. It contains the libraries and the source files (src folder).
    
##### VersalDriver Folder:
This folder is for DEMO purposes and contains the following folders and files:
* **`driver.py`**: This is the Python script that connects to the device using XSCT and run simulations on it. It provides a simple command line where user can run the simulation, read the output from the device, and visualize it.
* **`capture.py`**: This is the Python script that captures the serial output of the device and displays it.
* **`config_gen.py`**: This is the Python script that generates the simulation configuration file for the AIE-Only system.
* **`hybrid_config_gen.py`**: This is the Python script that generates the simulation configuration file for the Heterogeneous system.
* **`show.py`**: This Python script plots and saves the output of the simulations to the Output folder.
* **`params.txt`**: This file contains the MLP parameters.
* **tvb_algo folder**: A Python script used for getting TVB datasets.
* **cache folder**: Contains the TVB datasets.
* **Images**: Contains the Init.bin, AIE-Only.bin, Hybrid.bin binary files which are initializing, AIE-Only, and Heterogeneous systems boot image files.
* **Data**: This folder is used by the `config_gen.py` and `hybrid_config_gen.py` scripts to write the generated configuration files to.
* **Output**: This folder is used by the `driver.py` and `show.py` scripts to write the output from the device and generated figues to.



#### Instructions to test the project:
In order to test the project, the demo folder **VersalDriver** can be used on a Linux machine. Please be noted that the scripts in this folder read/write files to the folder itself, so proper authorizations must be given.

1) In a terminal, run the `capture.py`.
```
./VersalDriver$ sudo python3 capture.py
```
This script connects and reads from the serial port that the Versal reside on. Since it is accessing the serial port, it requires access to the system files. That is why it is important to run this script with `sudo`. __Change the `SERIAL_PORT` address in the `capture.py` script to the address of the serial port that the Versal is connected to.__

2) In a seperate terminal, run the `driver.py` script using Python.
```
$ cd VersalDriver
./VersalDriver$ python3 driver.py
```

You do not need to use `sudo` for running this script, however this script needs to be able to write files to its folder. This script opens a process and connects to the `xsct` command line tool. Make sure that this tool is available and can be seen by this script. The `xsct` tool connects to the server where the Versal board is, and choose the Versal system as its target. Change the `VERSAL_TA` variable in the `driver.py` script if the Versal is not number 1 in the list of targets. The default value for this variable is 1.

After running this script, you see that the Versal system is initialized and a very simple command line environment opens in the `driver.py`.

3) The opened command line is a simple one which accepts 3 commands:
- __`run`__ which runs a single simulation on the Versal. __Since this is a demo, for every simulation the whole boot image is downloaded to the device which takes a long time.__ This command has the following structure:
```
>> run hybrid|aie-only tvb76|tvb192|tvb998 <speed>
```
First argument the `run` command takes is which system to use for simulation, `hybrid` for the Heterogeneous systems and `aie-only` for the AIE-Only system. Second argument specifies which of the 3 models to run. Note that only the Heterogeneous system can run the `tvb998` model. The third argument is the speed in which the signals travel in the brain and is a (float) number.

- __`read`__ which reads the output results of the last simulation that was performed from the Versal device and writes it to the Output folder in the form of a `.bin` file. The outputs of the AIE-Only and Heterogeneous systems are stored in seperate files, but they are overwritten by new simulation runs from the same system. __Please note only run this command after the simulation is done, as stated in the serial output from the system visible in `capture.py`.__ If the output size is too large, because of a large model or a long simulation, this command might take some time.

- __`show`__ which creates a plot from the output results of the simulation and saves it in the Output folder as `output_a.png` or `output_h.png` for AIE-Only and Heterogeneous systems respectively. It has the following structure:
```
>> show hybrid|aie-only all|<node_id>
```
The first argument specifies to plot the output of which system. The second argument specifies whether to plot the output of all the regions of the brain in the same plot (`all`) or to only plot the activity of one of the regions specified by the number of that region (`node_id`). This command read the `.bin` file in the Output folder, so as long as there is such file (even from past simulations), this command can be used and there is no need for `run` or `read` commands to necessarily be executed before this command.

---
##### Example
```
>> run hybrid tvb76 2.0
>> read
>> show hybrid all
```
This example runs the simulation of the TVB76 dataset using the Heterogeneous system with the propagation speed of 2.0. __After the simulation is done__, the `read` command is enterd to read the output from the device, and then the activity of all the regions is plotted using the `show` command. You can run the same command with a signal propagation speed of 10.0 and see the difference in the outputs.

---

The output of the Versal is visible in the terminal of the `capture.py` script. When running a simulation, one can see the process of system initalization and running the simulation. When the simulation is done, the amount of time it took to perform the simulation is shown in this terminal.





#### Instructions to build the project:

The __Heterogeneous.zip__ and __AIE-Only.zip__ are full project archives for Heterogeneous and AIE-Only systems. The following steps show how to open these projects:

1) Open Vitis IDE 2022.2 and choose/create a workspace.
2) From the top menu, choose File->Import...
3) In the window that opens choose "Eclipse workspace or zip file" and click next.
4) In the next step, choose "Select archive file" and choose the project archive file.
5) From the list of projects, __deselect__ anything that is not in the following list:
    - base_pfm_vck190
    - ps_pfm_vck190
    - hybryd_system_system/nmm_system
    - hw_kernels
    - hybrid_system_system_hw_link/nmm_system_hw_link
    - hybrid_system/nmm
    - ps_app_system
    - ps_app
6) Click Finish.
7) When the importing process is finished, choose the "Hardware" build configuration for the hybrid_system_system/nmm_system project (the arrow next to the hammer icon) and build the project (the hammer icon).
8) After the compilation is finished, the final project can be found in the "Hardware/package/BOOT.bin" path under the hybrid_system_system/nmm_system project folder.

The compilation process for both the systems takes a long time, usually in the range of hours. That is why the Image files are provided in the VersalDriver folder for easier testing.