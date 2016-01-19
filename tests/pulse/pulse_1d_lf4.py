#!/usr/bin/env python

from elastic_wave.elastic import *
from elastic_wave.helpers import *
from firedrake import *
import numpy
from pyop2.profiling import timed_region

Lx = 4.0
h = 1e-2
with timed_region('mesh generation'):
    mesh = IntervalMesh(int(Lx/h), Lx)
elastic = ElasticLF4(mesh, "DG", 1, dimension=1)

# Constants
elastic.density = 1.0
elastic.dt = 0.0025
elastic.mu = 0.25
elastic.l = 0.5

print "P-wave velocity: %f" % Vp(elastic.mu, elastic.l, elastic.density)
print "S-wave velocity: %f" % Vs(elastic.mu, elastic.density)

F = FunctionSpace(elastic.mesh, "DG", 1)
elastic.absorption_function = Function(F)
elastic.absorption = Expression("x[0] >= 3.5 || x[0] <= 0.5 ? 100.0 : 0")

# Initial conditions
uic = Expression('exp(-50*pow((x[0]-1), 2))')
elastic.u0.assign(Function(elastic.U).interpolate(uic))
sic = Expression('-exp(-50*pow((x[0]-1), 2))')
elastic.s0.assign(Function(elastic.S).interpolate(sic))

T = 2.0
elastic.run(T)
