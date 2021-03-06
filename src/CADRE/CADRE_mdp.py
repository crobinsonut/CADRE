from openmdao.main.api import Assembly
from openmdao.main.datatypes.api import Float, Array, Int
import numpy as np
from .CADRE_assembly import CADRE
from pyopt_driver import pyopt_driver
from openmdao.lib.drivers.api import CONMINdriver
import os


class CADRE_Optimization(Assembly):

    def __init__(self, n=1500, m=300, npts=6):
        super(CADRE_Optimization, self).__init__()

        # add SNOPT driver
        self.add("driver", pyopt_driver.pyOptDriver())
        self.driver.optimizer = "SNOPT"
        self.driver.options = {'Major optimality tolerance': 1e-4,
                               'Iterations limit': 500000000,
                               "New basis file": 10}
        if os.path.exists("fort.10"):
            self.driver.options["Old basis file"] = 10

        #self.add("driver", CONMINdriver())

        # Raw data to load
        fpath = os.path.dirname(os.path.realpath(__file__))
        solar_raw1 = np.genfromtxt(fpath + '/data/Solar/Area10.txt')
        solar_raw2 = np.loadtxt(fpath + "/data/Solar/Area_all.txt")
        comm_rawGdata = np.genfromtxt(fpath + '/data/Comm/Gain.txt')
        comm_raw = (10 ** (comm_rawGdata / 10.0)).reshape(
            (361, 361), order='F')
        power_raw = np.genfromtxt(fpath + '/data/Power/curve.dat')

        # Load launch data
        launch_data = np.loadtxt(fpath + "/data/Launch/launch1.dat")

        # orbit position and velocity data for each design point
        r_e2b_I0s = launch_data[1::2, 1:]

        # number of days since launch for each design point
        LDs = launch_data[1::2, 0] - 2451545

        # LDs = [5233.5, 5294.5, 5356.5, 5417.5, 5478.5, 5537.5]

        # r_e2b_I0s = [np.array([4505.29362, -3402.16069, -3943.74582,
        #                        4.1923899, -1.56280012,  6.14347427]),
        #              np.array(
        #                  [-1005.46693,  -597.205348, -6772.86532, -0.61047858,
        #                   -7.54623146,  0.75907455]),
        #              np.array(
        #                  [4401.10539,  2275.95053, -4784.13188, -5.26605537,
        #                   -1.08194926, -5.37013745]),
        #              np.array(
        #                  [-4969.91222,  4624.84149,  1135.9414,  0.1874654,
        #                   -1.62801666,  7.4302362]),
        #              np.array(
        #                  [-235.021232,  2195.72976,  6499.79919, -2.55956031,
        #                   -6.82743519,  2.21628099]),
        #              np.array(
        #                  [-690.314375, -1081.78239, -6762.90367,  7.44316722,
        #                   1.19745345, -0.96035904])]

        # build design points
        for i in xrange(npts):
            i_ = str(i)
            aname = ''.join(["pt", str(i)])
            self.add(aname, CADRE(n, m, solar_raw1, solar_raw2,
                                  comm_raw, power_raw))
            self.get(aname).set("LD", LDs[i])
            self.get(aname).set("r_e2b_I0", r_e2b_I0s[i])

            # add parameters to driver
            self.driver.add_parameter("pt%s.CP_Isetpt" % i_, low=0., high=0.4)

            self.driver.add_parameter("pt%s.CP_gamma" % i_, low=0,
                                      high=np.pi / 2.)

            self.driver.add_parameter("pt%s.CP_P_comm" % i_, low=0., high=25.)

            param = ''.join(["pt", str(i), ".iSOC[0]"])
            self.driver.add_parameter(param, low=0.2, high=1.)

            # add constraints
            constr = ''.join(["pt", str(i), ".ConCh <= 0"])
            self.driver.add_constraint(constr)

            constr = ''.join(["pt", str(i), ".ConDs <= 0"])
            self.driver.add_constraint(constr)

            constr = ''.join(["pt", str(i), ".ConS0 <= 0"])
            self.driver.add_constraint(constr)

            constr = ''.join(["pt", str(i), ".ConS1 <= 0"])
            self.driver.add_constraint(constr)

            constr = ''.join(["pt", str(i), ".SOC[0][0] = pt",
                              str(i), ".SOC[0][-1]"])
            self.driver.add_constraint(constr)

        cell_param = ["pt%s.cellInstd" % str(i) for i in xrange(npts)]
        self.driver.add_parameter(cell_param, low=0, high=1)

        finangles = ["pt" + str(i) + ".finAngle" for i in xrange(npts)]
        antangles = ["pt" + str(i) + ".antAngle" for i in xrange(npts)]
        self.driver.add_parameter(finangles, low=0, high=np.pi / 2.)
        self.driver.add_parameter(antangles, low=-np.pi / 4, high=np.pi / 4)

        # add objective
        obj = ''.join([''.join(["-pt", str(i), ".Data[0][-1]"])
                      for i in xrange(npts)])
        self.driver.add_objective(obj)
