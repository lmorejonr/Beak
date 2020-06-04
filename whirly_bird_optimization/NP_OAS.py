import numpy as np 
import openmdao.api as om 

from openaerostruct.geometry.utils import generate_mesh
from openaerostruct.geometry.geometry_group import Geometry
from openaerostruct.aerodynamics.aero_groups import AeroPoint

from aerodynamics_geom_group import AerodynamicsGeomGroup

from cruise_oas import prob as COAS

# need to import optimized geometry and add a vector of size 2 for angle of attack 
# with the optimized alpha and a slightly smaller alpha with dα = .001 or something

# run a for loop for cg where val=np.array(i 0 0) where i loops from 0 to chord length 
# in increments of .01 or something and pull out Cm

# run a finite difference method analysis in an if statement where you say (Cm2-Cm1) / (dα) 
# and when the result is zero, pass that cg point along as the neutral point

shape = (2,)

prob = om.Problem()
c = COAS['wing_chord']
b = COAS['wing_span']

for x in range(0, 101, 1): # need to define c from previous optimized geometry
    RP = x * c / 100
    print(RP)

    indep_var_comp = om.IndepVarComp()
    indep_var_comp.add_output('v', val=50, units='m/s')
    indep_var_comp.add_output('Mach_number', val=0.3)
    indep_var_comp.add_output('re', val=1.e6, units='1/m')
    indep_var_comp.add_output('rho', val=1.225, units='kg/m**3')
    # indep_var_comp.add_output('cg', val=np.zeros((3)), units='m')
    indep_var_comp.add_output('cg', val=np.array([RP, 0, 0]))
    indep_var_comp.add_output('alpha', val=np.array([2, 2.001]))
    # indep_var_comp.add_output('alpha1', val=2)
    # indep_var_comp.add_output('alpha2', val=2.001)

    prob.model.add_subsystem('prob_vars' + str(x), indep_var_comp, promotes=['*'])

    # prob.model.add_subsystem('AerodynamicsGroup', AerodynamicsGeomGroup(shape=shape), promotes=['*'])

    mesh_dict = {'num_y' : 15,
                'num_x' : 7,
                'wing_type' : 'rect',
                'symmetry' : True,
                'span' : b,
                'chord' : c,
                }

    mesh = generate_mesh(mesh_dict)



    surface = { 'name' : ('wing' + str(x)), 
                'symmetry' : True,
                'S_ref_type' : 'wetted',
                'twist_cp' : np.zeros(2),
                'mesh' : mesh,
                'CL0' : 0.0,
                'CD0' : 0.001,
                'k_lam' : 0.05,
                't_over_c_cp' : np.array([0.1875]),
                'c_max_t' : 0.1,
                'with_viscous' : True,
                'with_wave' : False,
                'sweep' : 0.,
                'alpha' : 0.,
                }

    geom_group = Geometry(surface=surface)

    prob.model.add_subsystem(surface['name'], geom_group)

    aero_group = AeroPoint(surfaces=[surface])
    point_name = 'aero_point_0' + str(x)
    prob.model.add_subsystem(point_name, aero_group)

    # Connect flow properties to the analysis point
    prob.model.connect('v', point_name + '.v')
    prob.model.connect('alpha', point_name + '.alpha')
    prob.model.connect('Mach_number', point_name + '.Mach_number')
    prob.model.connect('re', point_name + '.re')
    prob.model.connect('rho', point_name + '.rho')
    prob.model.connect('cg', point_name + '.cg')

    name = 'wing' + str(x)

    # Connect the mesh from the geometry component to the analysis point
    prob.model.connect(name + '.mesh', point_name + '.' + name + '.def_mesh')

    # Perform the connections with the modified names within the
    # 'aero_states' group.
    prob.model.connect(name + '.mesh', point_name + '.aero_states' + '.' + name + '_def_mesh')
    # prob.model.connect('wing.t_over_c', 'aero_point_0.wing_perf.t_over_c')

    # Cmalpha = (prob[point_name + '.CM'][1] - prob[point_name + '.CM'][0]) / (prob['alpha'][1] - prob['alpha'][0])

    # if Cmalpha == 0:
    #     NP = x
    #     break
    # else:
    #     Cmalpha.clear
    #     continue

    ## - - - - - - - - - - - (maybe write another script for optimization and visusalization)

    # prob.driver = om.ScipyOptimizeDriver()

    # recorder = om.SqliteRecorder("aero_wb.db")
    # prob.driver.add_recorder(recorder)
    # prob.driver.recording_options['record_derivatives'] = True
    # prob.driver.recording_options['includes'] = ['*']

    # # # Setup problem and add design variables, constraint, and objective
    # prob.model.add_design_var(name + '.twist_cp', lower=-20., upper=20.)
    # prob.model.add_design_var
    # prob.model.add_design_var(name + '.sweep', lower=0., upper=50.)
    # prob.model.add_design_var(name + '.alpha', lower=0., upper=10.)
    # prob.model.add_constraint(point_name + '.wing_perf.CL', equals=0.5)
    # ## add onstraints and designvaraibles 
    # prob.model.add_objective(point_name + '.wing_perf.CD', scaler=1e4)

    # print(prob[point_name + '.CM'])

    # Set up the problem
    prob.setup()

    prob.run_model()
    prob.model.list_outputs(prom_name=True)

    # # plot_wing aero_wb.db to plot wing over iterations
    # # plot_wingbox aero_wb.db of CS of airfoil (but produces error, yet to fix)