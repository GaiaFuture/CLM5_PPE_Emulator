# The CLM5 Parameter Perturbation Experiment Emulator
## Understanding the Influence of Parameter Value Uncertainty on Climate Model Output: Developing an Interactive Dashboard

![image](https://github.com/GaiaFuture/CLM5_PPE_Emulator/assets/141206781/bca7cef5-9b6d-40a9-95a5-f2f2b8c0adc2)

This is a capstone project for the [Master of Environmental Data Science](https://bren.ucsb.edu/masters-programs/master-environmental-data-science) at [Bren School of Environmental Science and Management, University of California, Santa Barbara](https://bren.ucsb.edu)

#### Contributor Information:
Name: [Sofia Ingersoll](https://github.com/saingersoll)
Institution: Bren School of Environmental Science & Management -- UCSB

Name: [Heather Childers](https://github.com/hmchilders) 
Institution: Bren School of Environmental Science & Management -- UCSB

Name: [Sujan Bhattarai](https://github.com/Sujan-Bhattarai12)
Institution: Bren School of Environmental Science & Management -- UCSB

Faculty Advisor/Client: Dr. Daniel Kennedy 
Institution: NCAR Climate and Global Dynamics Lab -- UCSB

#### Principal Investigator Contact Information 
Name: Sofia Ingersoll
Email: singersoll@bren.edu

### Metadata
https://doi.org/10.5061/dryad.vq83bk422
   
### Project Summary
The data utilized in this repository was data derived from another source, University of California, Santa Barbara – Climate and Global Dynamics Lab, National Center for Atmospheric Research: Parameter Perturbation Experiment (CGD NCAR PPE-5).

To access the data generated for our Docker containerized interactive panel dashboard, visit [our Dryad data repo](https://datadryad.org/stash/dataset/doi:10.5061/dryad.vq83bk422). Full details on how the data was generated, alongside the relationships between the data are clearly outlined. By exploring the code in this repo, you'll see that the raw data from CGD NCAR PPE-5 is read in, wrangled to reduce the dimensions and properly weigh the time and grid cell dimensions. This data is stored under the `preprocessed_data` folder. This preprocessed data is then utilized to train our Gaussian Process Regression (GPR) emulator. The trained GPR Emulator is saved and stored for later use, alongside all of it's predictions, and necessary testing values for visualizing later in the `emulation_results` folder. Two visualizations are generated using the GPR data, a plot to show 1 input parameter vs 1 climate variable interaction predictions with 3 stdev of uncertainty. This plot serves as an interest meter to assess how influential and interesting a relationship is. The second plot applies Fourier Amplitude Sensitivity Transformation (FAST) to provide insights into how much each input parameter is contributing and influencing the climate variable outcome predictions. Inside of this plot is an inset plot displaying a cross validation of the climate variable test vs the climate variable GPR prediction. The R^2 is provided as well to provide transparency about our emulator's accuracy. Both of these visualizations may be found as png in the `plots` folder, under their respective folder names `emulator` and `FAST_accuracy_plots`. 

The contents of this repo that specifically pertain the the dashboard structure may be found in the `src` folder. Content relating the the Dockerization of the dashboard are located in the `web-app-helm` folder and `Dockerfile`. These files allow for continuous web-integration on the NCAR server overtime. At this point in time, the NCAR Software team has been engaged to publicly display our interactive dashboard under the National Center for Atmospheric Research – Climate and Global Dynamics Lab: Parameter Perturbation Experiment (NCAR – CGD: PPE) Directory. It is currently in the queue to be publicly accessible and the link to public facing dashboard will be added **here** once the dashboard is fully integrated into server.

#### Links/relationships to ancillary data sets:
The Parameter Perturbation Experiment data leveraged by our project was generated utilizing the [Community Land Model v5 (CLM5) predictions](https://www.earthsystemgrid.org/dataset/ucar.cgd.ccsm4.CLM_LAND_ONLY.html). If you'd like to look at NCAR's only public version of the data currently available, you can check it out [here](https://webext.cgd.ucar.edu/I2000/PPEn11_OAAT/). The data leveraged in this project is currently stored on the NCAR server and is not publicly available. If you'd like to learn more about this complex data, check out this [amazing presentation](https://www.cgd.ucar.edu/events/seminar/2023/katie-dagon-and-daniel-kennedy-132940 ) by Katie Dragon & Daniel Kennedy.

##### Additional ancillary data sets that are helpful to refer to include:
- [Visual example of the Community Land Model v5 (CLM5) climate model components and their respective parameter interactions](https://www.cesm.ucar.edu/models/clm).
- [Table of output variables for the Community Earth Systems Model v2 (CESM2) Large Ensemble Community Project](https://www.cesm.ucar.edu/community-projects/lens2/output-variables). CESM2 is the climate model that supersedes the CLM5. The predictions provided for the CESM2 output variables were leveraged by the CLM5 to produce its predictions. The variables available in CESM2 are accessible using our dashboard linked above. 
- [Table of specifications for the Community Land Model v5 (CLM5)](https://www.cesm.ucar.edu/models/clm/data)

### DATA & FILE OVERVIEW
```
├── emulation results/
│   └── f"{var_name}_{param_name}_{time_selection}_gpr_model.sav”
│   
├── plots/
│   ├── emulator/
|	└── f'emulator_plot_{var_name}_{param_name_upper}_{time_selection}_gpr_model.png
│   ├── FAST_accuracy_plot/
|	└── f'fast_acc_plot_{var_name}_{param_name}_{time_selection}.png
|
├── preprocessed_data
│   └── f"{var}_{time_selection}.nc"
|
├── scr
|   ├── final_workflow.py
|   ├── ppe_viz.py
|   ├── utils.py
|
├── web-app-helm
|   ├── templates
|   	├── deployment.yaml
|   	├── ingress.yaml
|   	├── service.yaml
|   ├── Chart.yaml
|   ├── helmignore.txt
|   ├── values.yaml
|
├── Dockerfile
|
├── README.md
├── environment.yml
├── requirements.txt
```

#### File List:
`Preprocessed Data Folder`
Content: 
We were working inside of NCAR’s CASPER cluster HPC server, this enabled us direct access to the raw data files. We created a script to read in 500 LHC PPE simulations as a data set with inputs for a climate variable and time range. When reading in the cluster of simulations, there is a preprocess function that performs dimensional reduction to simplify the data set for wrangling later. Once the data sets of interest were loaded, they were then ready for some dimensional corrections – some quirks that come with using CESM data. Our friend’s at NCAR CGDL actually provided us with the correct time-paring bug. The other functions to weigh each grid cell by land area, properly weigh each month according to their contribution to the number of days in a year, and to calculate the global average of each simulation were generated by our team to wrangle the data so it is suitable for emulation. These files were saved so they could be leveraged later using a built-in if-else statement within the `read_n_wrangle()` function found in `src/utils.py`. 

Cleaned subsets of 500 simulations from the PPE Latin Hypercube (LHC) data sets that are suitable for usage in a Gaussian Process Regression Machine Learning (GPR ML) Emulator. Dimensions are (500,1) for the perturbed parameter LHC simulations.  The subsets differ by user selected time range and climate variable of interest. The time ranges include: 1995-2015, 2000-2015, 2005-2015, 2010-2015. There are 11 climate variables in this folder, each containing a full set of time range subsets. The list includes: GPP, NBP, TOTVEGC, TLAI, EFLX_LH_TOT, SOILWATER_10CM, QRUNOFF, FSR, FAREA_BURNED, SNOWDP, LNC. These were selected due to popularity and ‘LNC’ was selected to assist with quality assurance measures that will be covered in detail further below. The `preprocessed_data` files are the inputs utilized to generate the `emulated_data`. Each preprocessed file was used to train the GPR ML emulator to produce a respective output for each climate variable and parameter for the time period of interest.

File naming convention: f"{var}_{time_selection}.nc"

File attributes: The dimensions of the preprocessed LHC perturbed parameter simulations are (500,1)

`Emulation Results Folder`
Content: 
The preprocessed data is then used in the GPR ML Emulator to make 100 predictions for a climate variable of interest and 32 individual parameters. To summarize briefly without getting too into the nitty gritty, our GPR emulator does 4 things:
- Simplifies the LHC data so it can look at 1 parameter at a time and assess its relationship with a climate variable
- Applies Fourier Amplitude Sensitivity Analysis to identify relationships between parameters and climate variables. It helps us see what the key influencers are.
- In the full chaotic LHC, it can assess the covariance of the parameter-parameter predictions simultaneously (this is the R^2 value you’ll see on your accuracy inset plot later)
- Additionally, it ‘pickles’ and saves the predictions and trained gpr_model so they can be utilized for further analysis, exploration, and visualizations.

Files contain our ‘pickled emulator’. In other words, the files contain character streams of the data generated by the trained GPR ML Emulator that are easy for your disk to unpack and use for more predictions and visualizations.These 100 predictions for each relationship were stored in a pickled dictionary that are then applied in the plotting functions below that were used to generate the pngs. 

File naming convention : f"{var_name}_{param_name}_{time_selection}_gpr_model.sav”

File attributes: results_dict
- results_dict is a dictionary that contains the 100 predictions + uncertainty, necessary values to make new predictions, and the trained emulator for all 11 climate variables against each of the 32 parameters.
  
```{python}
results_dict = {
    # perturbed parameter test values
   	 'X_values': {},
    # climate variable predictions
   	 'y_pred': {},
# climate variable predictions standard deviation
   	 'y_std': {},
		 # the trained GPR ML model
   	 'gpr_model': gpr_model,
		 # y_test to use to calculate R^2 later
   	 'y_test': y_test,
	‘X_test’: X_test
```

`Plots Folder`
##### FAST_accuracy_plots/
Content:
File naming convention:f'fast_acc_plot_{var_name}_{param_name}_{time_selection}.png
##### emulator/
Content:
File naming convention: f'emulator_plot_{var_name}_{param_name_upper}_{time_selection}_gpr_model.png
 
### METHODOLOGICAL INFORMATION
#### Description of methods used for collection/generation of data:

Attributes and structures defined in this [notebook](https://github.com/GaiaFuture/Prototype/blob/main/Data_Generation_Data_Repo.ipynb) outlines the workflow utilized to generate the data in this repo. It pulls functions from this [utils.py](https://github.com/GaiaFuture/Prototype/blob/main/utils.py) to execute the desired commands. Below we will look at the [utils](https://github.com/GaiaFuture/Prototype/blob/main/utils.py) functions that are not explicitly defined in the notebook. – General side note: if you decide to explore that Attributes and structures defined in this [notebook](https://github.com/GaiaFuture/Prototype/blob/main/Data_Generation_Data_Repo.ipynb) explaining how the data was made, you’ll notice you’ll be transported to another repo in this Organization:GaiaFuture. That’s our prototype playground! It’s a little messy because that’s where we spent the second half of this project tinkering. The official repository is https://github.com/GaiaFuture/CLM5_PPE_Emulator.

To access the data generated for our Docker containerized interactive panel dashboard, visit [our Dryad data repo](https://datadryad.org/stash/dataset/doi:10.5061/dryad.vq83bk422). Full details on how the data was generated, alongside the relationships between the data are outlined here.

### Instrument- or software-specific information needed to interpret the data: 
 - cartopy=0.22.0
  - dask=2024.1.0
  - dask-jobqueue=0.8.5
  - gpflow=2.5.2
  - hvplot=0.9.2
  - ipython=8.22.2
  - jupyter=1.0.0
  - jupyterlab=4.1.5
  - netcdf4=1.6.5
  - notebook=7.1.2
  - numpy=1.26.4
  - pandas=2.2.1
  - panel=1.3.8
  - plotly=5.19.0
  - python=3.11.7
  - regionmask=0.12.1
  - scikit-learn=1.4.1
  - scipy=1.12.0
  - seaborn=0.13.1
  - shapely=2.0.3
  - sparse=0.15.1
  - statsmodels=0.14.1
  - xarray=2024.2.0
  - xesmf=0.8.4

### Environmental/experimental conditions:
Once the Technical Documentation for this project is available, there is a significant section in the Solution Design dedicated to different kernel components that may be combined to better optimize the emulator.
Current kernel specification for Dashboard GPR Emulator:
```{python}
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# ----	Kernel Specs No Tuning	----
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Kernel Specs No Tuning
	kernel = ConstantKernel(constant_value=3, constant_value_bounds=(1e-2, 1e4))  \
        	* RBF(length_scale=1, length_scale_bounds=(1e-4, 1e8))
```

#### Missing data codes: 
There isn’t any present in this data, however there is opportunity for this in one section of the workflow outlined in the [notebook](https://github.com/GaiaFuture/Prototype/blob/main/Data_Generation_Data_Repo.ipynb) for `units_dict`. The output would look something like this:
`units_dict`:[ var_name: units: ’Unknown’ ]
If no units are present in the ds you’re reading from.

#### Specialized formats or other abbreviations used:
This table is a life line when deciphering the CESM data abbreviations. It is important to note that the dashboard will include a table of the 32 parameters and top 10 most common climate variables with a brief description of each, their Earth systems category, and 
Table of specifications for the Community Land Model v5 (CLM5) https://www.cesm.ucar.edu/models/clm/data

### Licenses/restrictions placed on the data:
This data is open source and available for climate scientists to leverage for climate model calibrations and identification of key climate influencers.

#### Recommended citation for the project:
Ingersoll Sofia, Childers Heather, Bhattarai Sujan. “Understanding the Influence of Parameter Value Uncertainty on Climate Model Output: Developing an Interactive Dashboard”. (2024). University of California, Santa Barbara – Bren School of Environmental Science & Management. https://github.com/GaiaFuture/CLM5_PPE_Emulator.

-![image](https://github.com/GaiaFuture/CLM5_PPE_Emulator/assets/141206781/f405f2f3-755f-4ffb-976b-2555f9bee29b)

#### Acknowledgements
Our team would like to say a special thank you to Dr. Linnia Hawkins and Nick Cote at NCAR for their collaboration throughout this project. Additionally, we would like to thank our Client and Faculty Advisor Dr. Daniel Kennedy and our Capstone Course Director Dr. Carmen Galaz-Garcia for their dedication to our team for the total duration of this project. We could not have achieved this without your collective guidance. Thank you!

This README.md file was generated on 2024-05-22 by SOFIA INGERSOLL
