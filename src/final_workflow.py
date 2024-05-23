import xarray as xr
from utils import * 

# Request an additional 10 cores of power for processing from the server
client = get_cluster("UCSB0021", cores = 30)
# apply peer2peer network communication across multiple devices
client.cluster

port=sys.argv[1]

def dashboard_wrangling(param, var, time_selection):
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ----    Subset User Selection Funct     ----
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    params, var_avg, param_name, var_name = read_n_wrangle(param, var, time_selection)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ----       Train Emulator Function      ----
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  
    results_dict = train_emulator(params, var_avg, var_name, time_selection)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ----       Plot Emulation Function      ----
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
    fig1 = plot_emulator2(results_dict, var_name, param_name, param_names_dict, time_selection)
    
    # Return plot
    return fig1


class Selections(param.Parameterized):
    parameter = param.Selector(objects=['leafcn'])
    variable = param.Selector(objects=['GPP', 'NBP', 'TOTVEGC', 'TLAI', 'EFLX_LH_TOT', 'SOILWATER_10CM', 'QRUNOFF', 'FSR', 'FAREA_BURNED', 'SNOWDP'])
    time_selection = param.Selector(objects=['2010-2015','2005-2015','2000-2015','1995-2015'])

    def view(self):
        # Call dashboard_wrangling with the selected parameter and variable
        fig1 = dashboard_wrangling(self.parameter, self.variable, self.time_selection)

        #Make the Panel object
        Plot_pane1 = pn.pane.Matplotlib(fig1)
        #Plot_pane2 = pn.pane.Matplotlib(fig2)

        # Return a Panel layout containing the converted Panel objects
        return Plot_pane1


def panel_app():
    obj = Selections()
    pn.Row(obj.view,obj.param)
    return pn.Row(obj.view,obj.param).servable()

pn.serve(panel_app, allow_websocket_origin=["localhost:"+port], port=int(port))