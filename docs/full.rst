==============================
Running the full CADRE problem
==============================

The previous tutorials provided short practical introductions to some of the
OpenMDAO components which are used in the CADRE problem. To run the full
CADRE problem:
    - Install the 'MBI' library
    - Obtain a license and source code for 'SNOPT <http://www.sbsi-sol-optimize.com/asp/sol_product_snopt.htm>'
    - Build and install `PyOpt <http://www.pyopt.org/>' with SNOPT support
    - Install pyopt_driver for OpenMDAO

The CADRE optimization problem can then by run by importing and running the
`CADRE_Optimization` assembly:

.. code-block:: python

    from openmdao.lib.casehandlers.api import CSVCaseRecorder
    from CADRE import CADRE_Optimization

    print "setting up"
    top = CADRE_Optimization(n=1500, m=300)
    top.driver.recorders = [CSVCaseRecorder(filename='CADRE.csv')]
    printvars = []
    for var in ['Data', 'ConCh', 'ConDs', 'ConS0', 'ConS1', 'SOC']:
        printvars += ["pt" + str(i) + ".Data" for i in xrange(6)]
    top.driver.printvars = printvars
    print "running"
    top.run()

This is implemented in `example.py`, in the top-level directory of the CADRE
plugin repository.
The purpose of the CSV case recorder is to save the state of the optimization
after each iteration of the assembly's driver. These iteration states will be
saved as lines in the file `CADRE.csv`. You can read from this file and
examine the performance of the optimization after the optimization has completed,
or even while the optimization is still occurring.

An example of how this file may be inspected:

.. code-block:: python

    import csv
    import numpy as np
    import pylab

    f = open("CADRE.csv", "rb")
    reader = csv.DictReader(f, skipinitialspace=True)

    X, Y, Z = [], [], []

    pcom = []

    for row in reader:
        data = [row["pt" + str(i) + ".Data[0][1499]"] for i in xrange(6)]
        sumdata = sum([float(i) for i in data if i])
        c1 = [row["Constraint ( pt" + str(i) + ".ConCh<=0 )"] for i in xrange(6)]
        c2 = [row["Constraint ( pt" + str(i) + ".ConDs<=0 )"] for i in xrange(6)]
        c3 = [row["Constraint ( pt" + str(i) + ".ConS0<=0 )"] for i in xrange(6)]
        c4 = [row["Constraint ( pt" + str(i) + ".ConS1<=0 )"] for i in xrange(6)]
        c5 = [row["Constraint ( pt" + str(i) + ".SOC[0][0]=pt" + str(i) + ".SOC[0][-1] )"]
              for i in xrange(6)]
        # c1_f = np.all([float(i) < 0 for i in c1 if i])
        # c2_f = np.all([float(i) < 0 for i in c2 if i])
        # c3_f = np.all([float(i) < 0 for i in c3 if i])
        # c4_f = np.all([float(i) < 0 for i in c4 if i])
        # c5_f = np.all([float(i) < 0 for i in c4 if i])

        c1_f = sum([float(i) for i in c1 if i])
        c2_f = sum([float(i) for i in c2 if i])
        c3_f = sum([float(i) for i in c3 if i])
        c4_f = sum([float(i) for i in c4 if i])
        c5_f = sum([float(i) for i in c5 if i])

        feasible = [c1_f, c2_f,  c3_f, c4_f, c5_f]

        X.append(sumdata), Y.append(sum(feasible)), Z.append(feasible)

        print sumdata

    Z = np.array(Z)
    if not len(Z):
        print "no data yet..."
        quit()
    pylab.figure()
    pylab.subplot(311)
    pylab.title("total data")
    pylab.plot(X, 'b')
    pylab.plot([0, len(X)], [3e4, 3e4], 'k--', marker="o")
    pylab.subplot(312)
    pylab.title("Sum of Constraints")
    pylab.plot([0, len(Y)], [0, 0], 'k--', marker="o")
    pylab.plot(Y, 'k')
    pylab.subplot(313)
    pylab.title("Max of Constraints")
    pylab.plot([0, len(Z)], [0, 0], 'k--')
    pylab.plot(Z[:, 0], marker="o", label="c1")
    pylab.plot(Z[:, 1], marker="o", label="c2")
    pylab.plot(Z[:, 2], marker="o", label="c3")
    pylab.plot(Z[:, 3], marker="o", label="c4")
    pylab.plot(Z[:, 4], marker="o", label="c5")
    pylab.legend(loc="best")
    pylab.show()

This is implemented in `readcsv.py`, in the top-level directory of the CADRE
plugin repository.

This will print the total data downloaded for each mdp at each iteration of
the optimization. This will also plot a figure containing three subplots, each
showing the iteration number on the horizontal axis.
The first subplot shows the data downloaded, the second shows the maximum value
taken over all constraints (a rough measure of feasibility, since all constraints
are satisfied by values <= 0), and finally the maximum constraint value across each of the 6
mdps, separated according to the 5 constraint types.

During the course of the optimization, the SNOPT optimizer will produce a
basis file, `fort.10`. In the event of a premature termination of the optimization,
SNOPT will automatically try to restart from the state determined by this file
the next time that the optimization is run in the same directory. If you would
rather cold-start the problem, this file can simply be deleted prior to
initializing an optimization if it exists.


