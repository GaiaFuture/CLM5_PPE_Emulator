import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import panel as pn
import param
import sys

port=sys.argv[1]

def plotter(c):
    fig =plt.Figure(figsize=[5,3])
    ax=fig.add_subplot(111)
    x=np.linspace(0,1,20)
    ax.plot(x,c*x)
    ax.set_ylim([0,3])
    ax.set_xlim([0,1])
    return fig

class Selections(param.Parameterized):
    v1   = param.Selector(objects=[1,2,3])
    def view(self):
        return plotter(self.v1)

def panel_app():
    obj = Selections()
    pn.Row(obj.view,obj.param)
    return pn.Row(obj.view,obj.param).servable()

pn.serve(panel_app, allow_websocket_origin=["localhost:"+port], port=int(port))
