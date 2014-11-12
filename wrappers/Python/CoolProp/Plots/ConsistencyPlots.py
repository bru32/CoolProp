from __future__ import division, print_function
import matplotlib
matplotlib.use('TKAgg')
import matplotlib.pyplot as plt
import numpy as np

import CoolProp as CP
from CoolProp.CoolProp import PropsSI
from CoolProp.Plots import PropsPlot

from matplotlib.backends.backend_pdf import PdfPages

all_solvers = ['PT', 'DmolarT', 'HmolarP', 'PSmolar', 'SmolarT', 'PUmolar', 'DmolarP', 'DmolarHmolar', 'DmolarSmolar', 'DmolarUmolar','HmolarSmolar','HmolarT','TUmolar','SmolarUmolar','HmolarUmolar']
not_implemented_solvers = ['SmolarUmolar','HmolarUmolar','TUmolar','HmolarT']

implemented_solvers = [pair for pair in all_solvers if pair not in not_implemented_solvers]

param_labels = dict(Hmolar = 'Enthalpy [J/mol]/1000',
                    Smolar = 'Entropy [J/mol/K]/1000',
                    Umolar = 'Int. Ener. [J/mol]/1000',
                    T = 'Temperature [K]',
                    Dmolar = 'Density [mol/m3]/1000',
                    P = 'Pressure [Pa]/1000')

def split_pair(pair):
    for key in ['Dmolar','Hmolar','Smolar','P','T','Umolar']:
        if pair.startswith(key):
            return key, pair.replace(key, '')
        
def split_pair_xy(pair):
    if pair == 'HmolarP':
        return 'Hmolar','P'
    elif pair == 'PSmolar':
        return 'Smolar','P'
    elif pair == 'PUmolar':
        return 'Umolar','P'
    elif pair == 'PT':
        return 'T','P'
    elif pair == 'DmolarT':
        return 'Dmolar','T'
    elif pair == 'SmolarT':
        return 'Smolar','T'
    elif pair == 'TUmolar':
        return 'Umolar','T'
    elif pair == 'HmolarT':
        return 'Hmolar','T'
    elif pair == 'DmolarP':
        return 'Dmolar','P'
    elif pair == 'DmolarHmolar':
        return 'Dmolar','Hmolar'
    elif pair == 'DmolarSmolar':
        return 'Dmolar','Smolar'
    elif pair == 'DmolarUmolar':
        return 'Dmolar','Umolar'
    elif pair == 'HmolarSmolar':
        return 'Smolar','Hmolar'
    elif pair == 'SmolarUmolar':
        return 'Smolar','Umolar'
    elif pair == 'HmolarUmolar':
        return 'Hmolar','Umolar'
    else:
        raise ValueError(pair)

class ConsistencyFigure(object):
    def __init__(self, fluid, figsize = (15, 23)):
        
        self.fluid = fluid
        self.fig, self.axes = plt.subplots(nrows = 5, ncols = 3, figsize = figsize)        
        self.pairs = all_solvers
        pairs_generator = iter(self.pairs)
        
        self.axes_list = []
        for row in self.axes:
            for ax in row:
                pair = pairs_generator.next()
                self.axes_list.append(ConsistencyAxis(ax, self, pair, self.fluid))
                ax.set_title(pair)

        self.calc_saturation_curves()
        self.plot_saturation_curves()
        
        self.calc_Tmax_curve()        
        self.plot_Tmax_curve()
        
        self.calc_melting_curve()
        self.plot_melting_curve()
        
        self.tight_layout()
        
        for i, (ax, pair) in enumerate(zip(self.axes_list, self.pairs)):
            if pair not in not_implemented_solvers:
                ax.consistency_check_singlephase()
            else:
                ax.cross_out_axis()
        
        
        self.fig.subplots_adjust(top=0.95)
        self.fig.suptitle('Consistency plots for '+self.fluid,size = 14)
    
    def calc_saturation_curves(self):
        """ 
        Calculate all the saturation curves in one shot using the state class to save computational time
        """
        HEOS = CP.AbstractState('HEOS', self.fluid)
        self.dictL, self.dictV = {}, {}
        for Q, dic in zip([0, 1], [self.dictL, self.dictV]):
            rhomolar,smolar,hmolar,T,p,umolar = [],[],[],[],[],[]
            for _T in np.logspace(np.log10(HEOS.keyed_output(CP.iT_triple)), np.log10(HEOS.keyed_output(CP.iT_critical)-1e-10), 300):
                try:
                    HEOS.update(CP.QT_INPUTS, Q, _T)
                    T.append(HEOS.T())
                    p.append(HEOS.p())
                    rhomolar.append(HEOS.rhomolar())
                    hmolar.append(HEOS.hmolar())
                    smolar.append(HEOS.smolar())
                    umolar.append(HEOS.umolar())
                except ValueError as VE:
                    print('sat error', VE)

            dic.update(dict(T = np.array(T), 
                            P = np.array(p), 
                            Dmolar = np.array(rhomolar), 
                            Hmolar = np.array(hmolar), 
                            Smolar = np.array(smolar), 
                            Umolar = np.array(umolar)))
    
    def plot_saturation_curves(self):
        for ax in self.axes_list:
            ax.label_axes()
            ax.plot_saturation_curves()
            
    def calc_Tmax_curve(self):
        HEOS = CP.AbstractState('HEOS', self.fluid)
        rhomolar,smolar,hmolar,T,p,umolar = [],[],[],[],[],[]
    
        for _p in np.logspace(np.log10(HEOS.keyed_output(CP.iP_min)*1.01), np.log10(HEOS.keyed_output(CP.iP_max)), 300):
            try:
                HEOS.update(CP.PT_INPUTS, _p, HEOS.keyed_output(CP.iT_max))
                T.append(HEOS.T())
                p.append(HEOS.p())
                rhomolar.append(HEOS.rhomolar())
                hmolar.append(HEOS.hmolar())
                smolar.append(HEOS.smolar())
                umolar.append(HEOS.umolar())
            except ValueError as VE:
                print('Tmax',VE)

        self.Tmax = dict(T = np.array(T),
                         P = np.array(p), 
                         Dmolar = np.array(rhomolar),
                         Hmolar = np.array(hmolar),
                         Smolar = np.array(smolar), 
                         Umolar = np.array(umolar))
    
    def plot_Tmax_curve(self):
        for ax in self.axes_list:
            ax.plot_Tmax_curve()
            
    def calc_melting_curve(self):
        state = CP.AbstractState('HEOS', self.fluid)
        rhomolar,smolar,hmolar,T,p,umolar = [],[],[],[],[],[]
        
        # Melting line if it has it
        if state.has_melting_line():
            pmelt_min = max(state.melting_line(CP.iP_min, -1, -1)*1.000001, state.keyed_output(CP.iP_triple))
            pmelt_max = min(state.melting_line(CP.iP_max, -1, -1)*0.999999, state.keyed_output(CP.iP_max))
            
            for _p in np.logspace(np.log10(pmelt_min), np.log10(pmelt_max), 100):
                try:
                    Tm = state.melting_line(CP.iT, CP.iP, _p)
                    state.update(CP.PT_INPUTS, _p, Tm)
                    T.append(state.T())
                    p.append(state.p())
                    rhomolar.append(state.rhomolar())
                    hmolar.append(state.hmolar())
                    smolar.append(state.smolar())
                    umolar.append(state.umolar())
                except ValueError as VE:
                    print('melting', VE)
        
        self.melt = dict(T = np.array(T),
                         P = np.array(p), 
                         Dmolar = np.array(rhomolar),
                         Hmolar = np.array(hmolar),
                         Smolar = np.array(smolar), 
                         Umolar = np.array(umolar))
        
    def plot_melting_curve(self):
        for ax in self.axes_list:
            ax.plot_melting_curve()
            
    def tight_layout(self):
        self.fig.tight_layout()
        
    def add_to_pdf(self, pdf):
        """ Add this figure to the pdf instance """
        pdf.savefig(self.fig)

class ConsistencyAxis(object):
    def __init__(self, axis, fig, pair, fluid):
        self.ax = axis
        self.fig = fig
        self.pair = pair
        self.fluid = fluid
        #self.saturation_curves()
        
    def label_axes(self):
        """ Label the axes for the given pair """
        xparam, yparam = split_pair_xy(self.pair)
        self.ax.set_xlabel(param_labels[xparam])
        self.ax.set_ylabel(param_labels[yparam])
        
        if xparam == 'P':
            self.ax.set_xscale('log')
        if yparam == 'P':
            self.ax.set_yscale('log')
    
    def plot_saturation_curves(self):
        xparam, yparam = split_pair_xy(self.pair)
        xL = self.to_axis_units(xparam, self.fig.dictL[xparam])
        yL = self.to_axis_units(yparam, self.fig.dictL[yparam])
        xV = self.to_axis_units(xparam, self.fig.dictV[xparam])
        yV = self.to_axis_units(yparam, self.fig.dictV[yparam])
        self.ax.plot(xL, yL, 'k', lw = 1)
        self.ax.plot(xV, yV, 'k', lw = 1)
        
    def plot_Tmax_curve(self):
        xparam, yparam = split_pair_xy(self.pair)
        x = self.to_axis_units(xparam, self.fig.Tmax[xparam])
        y = self.to_axis_units(yparam, self.fig.Tmax[yparam])
        self.ax.plot(x, y, 'r', lw = 1)
        
    def plot_melting_curve(self):
        xparam, yparam = split_pair_xy(self.pair)
        x = self.to_axis_units(xparam, self.fig.melt[xparam])
        y = self.to_axis_units(yparam, self.fig.melt[yparam])
        self.ax.plot(x, y, 'b', lw = 1)
            
    def to_axis_units(self, label, vals):
        """ Convert to the units used in the plot """
        if label in ['Hmolar', 'Smolar', 'Umolar', 'Dmolar', 'P']:
            return vals/1000
        elif label in ['T']:
            return vals
        else:
            raise ValueError(label)
            
    def consistency_check_singlephase(self):
        
        state = CP.AbstractState('HEOS', self.fluid)
        
        for p in np.logspace(np.log10(state.keyed_output(CP.iP_min)*1.01), np.log10(state.keyed_output(CP.iP_max)), 40):
            
            Tmin = state.keyed_output(CP.iT_triple)
            if state.has_melting_line():
                try:
                    pmelt_min = state.melting_line(CP.iP_min, -1, -1)
                    if p < pmelt_min:
                        T0 = Tmin
                    else:
                        T0 = state.melting_line(CP.iT, CP.iP, p)
                except Exception as E:
                    T0 = Tmin + 1.1
                    print('MeltingLine:', E)
            else:
                T0 = Tmin+1.1
                
            for T in np.linspace(T0, state.keyed_output(CP.iT_max), 40):
                state_PT = CP.AbstractState('HEOS', self.fluid)
                
                try:
                    # Update the state using PT inputs in order to calculate all the remaining inputs
                    state_PT.update(CP.PT_INPUTS, p, T)
                except ValueError as VE:
                    print('consistency',VE)
                    continue
                    
                # Update the state given the desired set of inputs
                param1, param2 = split_pair(self.pair)
                key1 = getattr(CP, 'i'+param1)
                key2 = getattr(CP, 'i'+param2)
                pairkey = getattr(CP, self.pair+'_INPUTS')
                
                _exception = False
                try:
                    state.update(pairkey, state_PT.keyed_output(key1), state_PT.keyed_output(key2))
                except ValueError as VE:
                    print(VE)
                    _exception = True
                    
                # Get the keys and indices and values for the inputs needed
                xparam, yparam = split_pair_xy(self.pair)
                xkey = getattr(CP, 'i' + xparam)
                ykey = getattr(CP, 'i' + yparam)
                x = self.to_axis_units(xparam, state.keyed_output(xkey))
                y = self.to_axis_units(yparam, state.keyed_output(ykey))
                
                if _exception:
                    self.ax.plot(x, y, 'k+', ms = 3)
                else:
                    # Check the error on the density
                    if abs(state_PT.rhomolar()/state.rhomolar()-1) < 1e-3 and abs(state_PT.p()/state.p()-1) < 1e-3 and abs(state_PT.T() - state.T()) < 1e-3:
                        self.ax.plot(x, y, 'k.', ms = 1)
                    else:
                        self.ax.plot(x, y, 'kx', ms = 3)
        
    def consistency_check_twophase(self):
        pass
        
    def cross_out_axis(self):
        xlims = self.ax.get_xlim()
        ylims = self.ax.get_ylim()
        self.ax.plot([xlims[0],xlims[1]],[ylims[0],ylims[1]],lw = 3,c = 'r')
        self.ax.plot([xlims[0],xlims[1]],[ylims[1],ylims[0]],lw = 3,c = 'r')
        
        xparam, yparam = split_pair_xy(self.pair)
        x = 0.5*xlims[0]+0.5*xlims[1]
        y = 0.5*ylims[0]+0.5*ylims[1]
        if yparam == 'P':
            y = (ylims[0]*ylims[1])**0.5
            
        self.ax.text(x,y,'Not\nImplemented',ha='center',va ='center',bbox = dict(fc = 'white'))

if __name__=='__main__':
    PVT = PdfPages('Consistency.pdf')
    for fluid in CP.__fluids__:
        print('************************************************')
        print(fluid)
        print('************************************************')
        ff = ConsistencyFigure(fluid)
        ff.add_to_pdf(PVT)
        plt.close()
        del ff
    PVT.close()