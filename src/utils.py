#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ----           load libraries           ----
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import pickle
import os

import glob
from dask_jobqueue import PBSCluster
from dask.distributed import Client

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.impute import SimpleImputer

from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, Matern, WhiteKernel,ConstantKernel
from sklearn.gaussian_process.kernels import ConstantKernel, RBF
from sklearn.metrics.pairwise import linear_kernel as Linear

from sklearn.metrics import make_scorer
from sklearn.preprocessing import MinMaxScaler 
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import accuracy_score
from sklearn.metrics import r2_score
from scipy.stats import norm
from scipy.fft import fft

import panel as pn
import param
pn.extension()
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ----  server request to aid processing  ----
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def get_cluster(account,cores=30):    
    """Spin up a dask cluster.

    Keyword arguments:
    account -- your account number, e.g. 'UCSB0021'
    cores -- the number of processors requested

    Returns:
    client -- can be useful to inspect client.cluster or run client.close()
    """

    cluster = PBSCluster(
    # The number of cores you want
    cores=1,
    # Amount of memory
    memory='10GB',
     # How many processes
    processes=1,
    # The type of queue to utilize (/glade/u/apps/dav/opt/usr/bin/execcasper)
    queue='casper', 
    # Use your local directory
    local_directory = '$TMPDIR',
    # Specify resources
    resource_spec='select=1:ncpus=1:mem=10GB',
    # Input your project ID here
    account = account,
    # Amount of wall time
    walltime = '02:00:00',
    )

    # Scale up
    cluster.scale(cores)
    
    # Setup your client
    client = Client(cluster)

    return client



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ----     cluster reading function       ----
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# modify the function if you want to pass the parameter
# pull 20 years of data
# this has cool potential to have time period subset option
# indexing the selected lists or using multiples of 500 
def read_all_simulations(var, time_selection):
    '''Prepare cluster list and read to create ensemble(group of data)
    Use preprocess to select only certain dimension and a variable'''
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #----  Define list of cluster lists ----
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # each cluster list contains 500 simulations to call
    cluster_lists = [
        
        # 1995 - 2000
        sorted(glob.glob('/glade/campaign/cgd/tss/projects/PPE/PPEn11_LHC/transient/hist/PPEn11_transient_LHC[0][0-5][0-9][0-9].clm2.h0.1995-02-01-00000.nc'))[1:],
        # 2000 - 2005
        sorted(glob.glob('/glade/campaign/cgd/tss/projects/PPE/PPEn11_LHC/transient/hist/PPEn11_transient_LHC[0][0-5][0-9][0-9].clm2.h0.2000-02-01-00000.nc'))[1:],
        # 2005 - 2010
        sorted(glob.glob('/glade/campaign/cgd/tss/projects/PPE/PPEn11_LHC/transient/hist/PPEn11_transient_LHC[0][0-5][0-9][0-9].clm2.h0.2005-02-01-00000.nc'))[1:],
         # 2010 - 2015
        sorted(glob.glob('/glade/campaign/cgd/tss/projects/PPE/PPEn11_LHC/transient/hist/PPEn11_transient_LHC[0][0-5][0-9][0-9].clm2.h0.2010-02-01-00000.nc'))[1:]
    ]

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #----    Prepping to Load Cluster   ----
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def preprocess(ds, var):
        '''using this function in xr.open_mfdataset as preprocess
        ensures that when only these four things are selected 
        before the data is combined'''
        return ds[['lat', 'lon', 'time', var]]

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #----   If-else Load Selected Time  ----
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Select appropriate lists based on the time_selection

     # Select appropriate lists based on the time_selection
    if time_selection == '2010-2015':
        selected_files = cluster_lists[3]
        
        # Read the list and load it for the notebook using combine='nested'
        ds = xr.open_mfdataset(selected_files, 
                               combine='nested',
                               preprocess=lambda ds: preprocess(ds, var),
                               parallel=True, 
                               concat_dim=["ens"])
    else:
        # up to list 1 aka 0 bc python index
        # python end exclusive so need to go up to 4 for all
        if time_selection == '1995-2015':
            selected_lists = cluster_lists[:4]
         # up to list 2 aka 1 bc python index
        elif time_selection == '2000-2015':
            selected_lists = cluster_lists[1:4]
         # up to list 3 aka 2 bc python index
        elif time_selection == '2005-2015':
            selected_lists = cluster_lists[2:4]
        # safety check
        else:
            # to ensure a user selects time range
            raise ValueError("Uh oh, please select a time range that is currently available.")

    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #----      Load in Cluster Data     ----
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # read the list and load it for the notebook
        ds = xr.open_mfdataset( selected_lists, 
                                combine='nested',
                               # lambda allows us to call the predefined preprocess on the ds
                                preprocess = lambda ds: preprocess(ds, var),
                                parallel= True, 
                                concat_dim= ["time", "ens"])

    # we aren't going to save these files because they need to be preprocessed 
    # using the wrangle and subset functions
    # better to keep these things broken up / shorter for future works updates
    # makes sense to keep if else pulling statement at the top of read_n_wrangle
    return ds
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ----     load data stored in casper     ----
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #----  Gridcell Landareas Data     -----
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# reading, storing, subsetting
landarea_file = '/glade/campaign/cgd/tss/projects/PPE/helpers/sparsegrid_landarea.nc'

landarea_ds = xr.open_dataset(landarea_file)

landarea = landarea_ds['landarea']
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #----        Parameter Data.       ----
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# store the parameter names to index later
param_names = {
        key.upper(): value for key, value in {
            'FUN_fracfixers': 0, 'KCN': 1, 'a_fix': 2, 'crit_dayl': 3, 'd_max': 4, 'fff': 5,
            'froot_leaf': 6, 'fstor2tran': 7, 'grperc': 8, 'jmaxb0': 9, 'jmaxb1': 10, 'kcha': 11,
            'kmax': 12, 'krmax': 13, 'leaf_long': 14, 'leafcn': 15, 'lmr_intercept_atkin': 16,
            'lmrha': 17, 'lmrhd': 18, 'medlynintercept': 19, 'medlynslope': 20, 'nstem': 21,
            'psi50': 22, 'q10_mr': 23, 'slatop': 24, 'soilpsi_off': 25, 'stem_leaf': 26,
            'sucsat_sf': 27, 'theta_cj': 28, 'tpu25ratio': 29, 'tpuse_sf': 30, 'wc2wjb0': 31
        }.items()
    }


def param_wrangling():
    # x parameter data for assessment
    df = pd.read_csv('/glade/campaign/asp/djk2120/PPEn11/csvs/lhc220926.txt',index_col=0)
    # the only dimension here is the 'member' aka file index id [LCH0001-500]
    # convert to xr.ds
    params = xr.Dataset(df)

    # list comprehension no need for empty list
    columns = [params[v].values for v in params.data_vars]


    # iterate over params
    return np.array(columns).T


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ----     correct time-parsing bug       ----
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def fix_time(da):
    
    '''fix CESM monthly time-parsing bug'''
    
    yr0 = str(da['time.year'][0].values)
    
    da['time'] = xr.cftime_range(yr0,periods=len(da.time),freq='MS',calendar='noleap')
    
    return da


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ----  weigh dummy landarea by gridcell  ----
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #----  Weight Gridcells by Landarea ----
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def weight_landarea_gridcells(da,landarea):

    # weigh landarea variable by mean of gridcell dimension
    return da.weighted(landarea).mean(dim = 'gridcell')

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ----       weight var data time dim     ----
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#------Weighted Averages by Time---
def yearly_weighted_average(da):
    # Get the array of number of days from the main dataset
    days_in_month = da['time.daysinmonth']

    # Multiply each month's data by corresponding days in month
    weighted_month = (days_in_month*da).groupby("time.year").sum(dim = 'time')

    # Total days in the year
    days_per_year = days_in_month.groupby("time.year").sum(dim = 'time')

    # Calculate weighted average for the year
    return weighted_month / days_per_year
    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ----    Subset User Selection Funct     ----
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def subset_var_cluster(var, time_selection):
    '''Subset the selected variable 
    (s) between 2005-2010 [for now, will be time range]
    as a xr.da.'''
    
    # Read in and wrangle user selected variable cluster
    da_v = read_all_simulations(var, time_selection)
    # feb. ncar time bug
    da = fix_time(da_v)
    # convert xr.ds to xr.da
    da = da[var]

    return da.compute()


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ----      Subset Var Wrangle Funct      ----
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def wrangle_var_cluster(da):
    '''Weight gridcell dimension by landarea 
    and weight time dimension by the days per each month
    over the total number of days in a year. Globally average
    the selected variable between 2005-2010 
    [for now, will be time range]
    as a xr.da.'''
    # weight gridcell dim by global land area
    da_global = weight_landarea_gridcells(da, landarea)
    # weight time dim by days in month
    da_global_ann = yearly_weighted_average(da_global)
    # take global avg for variable over year dimension
    var = da_global_ann.mean(dim='year')
    
    return var



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ----        Wrangle Data          ----
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def read_n_wrangle(param, var, time_selection):
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ----            Parameter Data.         ----
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # store user-inputs as global variables
    # will call later for plotting
    global param_name, var_name
    param_name = param
    var_name = var
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ----            Parameter Data.         ----
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # pull in parameter data
    params = param_wrangling()
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ----        If-else Load Data     ----
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    filepath = os.path.join("preprocessed_data", f"{var}_{time_selection}.nc")
    if os.path.exists(filepath):
         #read in the file as a dataset
        ds=xr.open_dataset('preprocessed_data/'+var+'_'+time_selection+'.nc')
    
        # then convert back to data array
        var_avg = ds[var]
    else:
        print(f"Reading and wrangling your data, this may take a few minutes")
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ----    Subset User Selection Funct     ----
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        var_da = subset_var_cluster(var, time_selection)

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ----      Subset Var Wrangle Funct      ----
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        var_avg = wrangle_var_cluster(var_da)

        # you ought to convert the data array to dataset before writing to file
        ds = var_avg.to_dataset(name = var)
        # note that this will throw error if you try to overwrite existing files
        ds.to_netcdf('preprocessed_data/'+var+'_'+time_selection+'.nc') 

    return params, var_avg, param_name, var_name

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ----        Create Params Dict    ----
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def create_parameter_names_dict():
    data = {
        key.upper(): value for key, value in {
            'FUN_fracfixers': 0, 'KCN': 1, 'a_fix': 2, 'crit_dayl': 3, 'd_max': 4, 'fff': 5,
            'froot_leaf': 6, 'fstor2tran': 7, 'grperc': 8, 'jmaxb0': 9, 'jmaxb1': 10, 'kcha': 11,
            'kmax': 12, 'krmax': 13, 'leaf_long': 14, 'leafcn': 15, 'lmr_intercept_atkin': 16,
            'lmrha': 17, 'lmrhd': 18, 'medlynintercept': 19, 'medlynslope': 20, 'nstem': 21,
            'psi50': 22, 'q10_mr': 23, 'slatop': 24, 'soilpsi_off': 25, 'stem_leaf': 26,
            'sucsat_sf': 27, 'theta_cj': 28, 'tpu25ratio': 29, 'tpuse_sf': 30, 'wc2wjb0': 31
        }.items()
    }
    return data 
    
# object to store in utils outside of any function so it's callable
param_names_dict = create_parameter_names_dict() 


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ----        Train Emulator        ----
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def train_emulator(param, var, var_name, time_selection):
     #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     # ----         Split Data           ----
     #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    X_train, X_test, y_train, y_test = train_test_split(param,
                                                        var, 
                                                        test_size=0.2,
                                                        random_state=0)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ----    Kernel Specs No Tuning    ----
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Kernel Specs No Tuning
    kernel = ConstantKernel(constant_value=3, constant_value_bounds=(1e-2, 1e4))  \
            * RBF(length_scale=1, length_scale_bounds=(1e-4, 1e8))

    # Using an out-of-the-box kernel for now
    gpr_model = GaussianProcessRegressor(kernel=kernel,
                                         n_restarts_optimizer=20, 
                                         random_state=99, 
                                         normalize_y=True)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ----         Fit the Model        ----
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Fit the model to the training data
    gpr_model.fit(X_train, y_train)

    # Prepare to store results
    results_dict = {
        'X_values': {},
        'y_pred': {},
        'y_std': {},
        'r2': {}
    }

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ----      Iterate thru Params     ----
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    for param_name, param_index in param_names_dict.items():
        # Create X_values for prediction linspace
        X_values = np.full((100, len(param_names_dict)), 0.5)           # r2 drops to 0.004 when removing this, but we're only using the R^2 used in fast plot
       # X_values = np.tile(X_test, 1)
        X_values[:, param_index] = np.linspace(0, 1, 100)
        # Vary only the current parameter over a linspace
        #X_values[:, param_index] = np.linspace(np.min(X_test[:, param_index]), np.max(X_test[:, param_index]))

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ----         Get Predictions      ----
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Make predictions for the current parameter
        y_pred, y_std = gpr_model.predict(X_values, return_std=True)

        
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ----         Collect Metrics      ----
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        mae = mean_absolute_error(y_test, y_pred)
        rmse_emulator = np.sqrt(mean_squared_error(y_test, y_pred))
        r2_emulator = np.corrcoef(y_test, y_pred)[0, 1]**2

        # Store results in dictionaries
        results_dict['X_values'][param_name] = X_values
        results_dict['y_pred'][param_name] = y_pred
        results_dict['y_std'][param_name] = y_std
        results_dict['r2'][param_name] = r2_emulator
        
   
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ----      Pickle Emulation     ----
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Save the predictions and overall R^2 to a file
        filename = os.path.join("emulation_results", f"{var_name}_{param_name}_{time_selection}_gpr_model.sav")

        if os.path.exists(filename):
            # Load the model from disk
            loaded_model = pickle.load(open(filename, 'rb'))
        else:
            print(f"Emulator is running for {param_name}, this may take a few moments")
            with open(filename, 'wb') as file:
                pickle.dump((X_values, y_pred, y_std, r2_emulator, param_name, var_name), file)

    return results_dict


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ----          Plot Emulator       ----
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 

# Create an array that sets the value of all 32 parameters to 0.5
# this will be used when plotting emulation
def plot_emulator2(results_dict, var_name, param_name, param_names_dict, time_selection):
    # Convert param_name to uppercase to match the filenames
    param_name_upper = param_name.upper()
    
    # Retrieve the data for the specific parameter
    X_values = results_dict['X_values'][param_name_upper]
    y_pred = results_dict['y_pred'][param_name_upper]
    y_std = results_dict['y_std'][param_name_upper]

    # Get the parameter index corresponding to the name
    indexed_param = param_names_dict[param_name_upper]

    # Calculate the z-score for the 99.7% confidence interval
    z_score = norm.ppf(0.99865)

    # Calculate global min and max for y limits based on the specific parameter's prediction
    global_min = np.min(y_pred - y_std)
    global_max = np.max(y_pred + y_std)

    # Plot the results
    fig = Figure(figsize=(10, 6), tight_layout = True)
    # Attach an Axes object to the figure
    ax1 = fig.add_subplot()  # First subplot
    #ax2 = fig.add_subplot(122)  # Second subplot
  
    # Load the Roboto font
    #plt.rcParams['font.family'] = 'Roboto'

    
    # Set the style to a dark theme
    plt.style.use('dark_background')
    #Plot the Predictions
    ax1.plot(X_values[:, indexed_param],
         y_pred,
         color='white',
         linewidth=3,
         label='GPR Prediction')

    # Apply z-score for 99.7% CI
    ax1.fill_between(X_values[:, indexed_param],
                    y_pred - z_score * y_std, y_pred + z_score * y_std,
                    alpha=0.5,
                    color='#62c900ff',
                    label='3 St.Dev., Confidence Interval')

    ax1.set_xlabel(f'Perturbed Parameter: {param_name.title()}', size=18)
    ax1.set_ylabel(f'Climate Variable: {var_name.split("_")[0].title()}', size=18)
    ax1.set_title(f'Parameter Perturbation Uncertainty Estimation \nAssessing Global Annual Means {time_selection}', size=24)
    ax1.legend(fontsize=16)

    # Customize ticks
    ax1.tick_params(axis='both', which='major', labelsize=14)

    # Set y limits based on global min and max
    ax1.set_ylim(global_min, global_max)

    # Save the plot as a PNG file
    plot_dir = 'plots/emulator'
    os.makedirs(plot_dir, exist_ok=True)
    fig.savefig(os.path.join(plot_dir, f'emulator_plot_{var_name}_{param_name_upper}_{time_selection}_gpr_model.png'))

    return fig

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ----      Plot FAST Accuracy      ----
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
def create_parameter_names_dict():
    data = {
        key.upper(): value for key, value in {
            'FUN_fracfixers': 0, 'KCN': 1, 'a_fix': 2, 'crit_dayl': 3, 'd_max': 4, 'fff': 5,
            'froot_leaf': 6, 'fstor2tran': 7, 'grperc': 8, 'jmaxb0': 9, 'jmaxb1': 10, 'kcha': 11,
            'kmax': 12, 'krmax': 13, 'leaf_long': 14, 'leafcn': 15, 'lmr_intercept_atkin': 16,
            'lmrha': 17, 'lmrhd': 18, 'medlynintercept': 19, 'medlynslope': 20, 'nstem': 21,
            'psi50': 22, 'q10_mr': 23, 'slatop': 24, 'soilpsi_off': 25, 'stem_leaf': 26,
            'sucsat_sf': 27, 'theta_cj': 28, 'tpu25ratio': 29, 'tpuse_sf': 30, 'wc2wjb0': 31
        }.items()
    }
    return data

def plot_FAST_accuracy(gpr_model, r2_emulator, y_test, y_pred, y_std):
    def gaussian_regression_lines(gpr_model):
        fourier_amplitudes = []
        
        for param_index in range(32):
            X_values = np.full((10, 32), 0.5)
            X_values[:, param_index] = np.linspace(0, 1, 10)
            y_pred, _ = gpr_model.predict(X_values, return_std=True)
            y_fft = fft(y_pred)
            amplitude = np.abs(y_fft)
            fourier_amplitudes.append(amplitude[1])

        return fourier_amplitudes

    fourier_amplitudes = gaussian_regression_lines(gpr_model)
    sorted_indices = np.argsort(fourier_amplitudes)
    sorted_fourier_amplitudes = np.array(fourier_amplitudes)[sorted_indices]
    swapped_param_keys = {v: k for k, v in create_parameter_names_dict().items()}
    sorted_parameter_names = [swapped_param_keys[index] for index in sorted_indices]

    fig, ax = plt.subplots(figsize=(16, 8))
    ax.barh(range(len(sorted_fourier_amplitudes)), sorted_fourier_amplitudes, color='darkolivegreen')
    ax.set_ylabel('')
    ax.set_xlabel('Fourier Amplitude')
    ax.set_title(f'Fourier Amplitude Sensitivity Test (FAST) for {var_name} vs {param_name}')
    ax.set_yticks(range(len(sorted_fourier_amplitudes)), sorted_parameter_names)
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    #ax.text(1, 0.5, f'R2_score = {np.round(r2_train,2)}', fontsize=10, transform=ax.transAxes)
    ax.set_aspect('auto', adjustable='box')

    # Create inset for accuracy plot
    ax_inset = inset_axes(ax, width="40%", height="40%", loc='center right')
    ax_inset.errorbar(y_test, y_pred, yerr=3*y_std, fmt="o", color='#134611')
    ax_inset.plot([0, np.max(y_test)], [0, np.max(y_pred)], linestyle='--', c='k')
    ax_inset.set_xlim([np.min(y_test)-1, np.max(y_test)+1])
    ax_inset.set_ylim([np.min(y_pred)-1, np.max(y_pred)+1])
    ax_inset.set_xlabel('Variable Test')
    ax_inset.set_ylabel(f'Emulated Variable: {var_name}')
    ax_inset.set_title(f'Emulator Accuracy: {var_name}')
    ax_inset.text(0.5, 0.1, f'R² Score = {np.round(r2_emulator, 2)}', fontsize=12, \
                  transform=ax_inset.transAxes, horizontalalignment='center', weight='bold')
    
     # Save the plot as a PNG file
    plt.savefig(f'plots/fast_accuracy/fast_acc_plot_{var_name}_{param_name}.png')

    return plt.show()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ----      Dashboard Wrangle       ----
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
