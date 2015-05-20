#!/usr/bin/env python

from firedrake import *
import os

# PETSc environment variables
try:
   if(os.environ["PETSC_OPTIONS"] == ""):
      os.environ["PETSC_OPTIONS"] = "-log_summary"
   else:
      os.environ["PETSC_OPTIONS"] = os.environ["PETSC_OPTIONS"] + " -log_summary"
except KeyError:
   # Environment variable does not exist, so let's set it now.
   os.environ["PETSC_OPTIONS"] = "-log_summary"
   
parameters['form_compiler']['quadrature_degree'] = 4
parameters["coffee"]["O2"] = False

Lx = 4.0
Ly = 1.0
h = 1e-2
mesh = RectangleMesh(int(Lx/h), int(Ly/h), Lx, Ly)

S = TensorFunctionSpace(mesh, "CG", 1)
U = VectorFunctionSpace(mesh, "CG", 1)
dimension = 2

v = TestFunction(S)
w = TestFunction(U)
s = TrialFunction(S)
u = TrialFunction(U)
s0 = Function(S)
u0 = Function(U)
s1 = Function(S)
u1 = Function(U)

# Constants
density = 1.0
T = 2.0
dt = 0.0025
mu = 0.25
l = 0.5

Vp = sqrt((l + 2*mu)/density) # P-wave velocity
Vs = sqrt(mu/density) # S-wave velocity

n = FacetNormal(mesh)

# Weak forms
#F_u = density*inner(w, (u - u0)/dt)*dx + inner(grad(w), s0)*dx #- inner(dot(jump(w), avg(s0)), n('+'))*dS - inner(dot(jump(w), avg(s0)), n('-'))*dS
#F_s = inner(v, (s - s0)/dt)*dx - inner(v, l*(div(u1))*Identity(dimension))*dx - inner(v, mu*(grad(u1) + grad(u1).T))*dx # - inner(dot(jump(v), avg(u1)), n('+'))*dS - inner(dot(jump(v), avg(u1)), n('-'))*dS

F_u = density*inner(w, (u - u0)/dt)*dx + inner(grad(w), s0)*dx
F_s = inner(v, (s - s0)/dt)*dx - inner(v, l*(div(u1))*Identity(dimension))*dx - inner(v, mu*(grad(u1) + grad(u1).T))*dx

problem_u = LinearVariationalProblem(lhs(F_u), rhs(F_u), u1)
solver_u = LinearVariationalSolver(problem_u)

problem_s = LinearVariationalProblem(lhs(F_s), rhs(F_s), s1)
solver_s = LinearVariationalSolver(problem_s)

output_u = File("velocity.pvd")
output_s = File("stress.pvd")

# Initial conditions
uic = Expression(('exp(-50*pow((x[0]-1), 2))', '0'))
u0.assign(Function(U).interpolate(uic))
sic = Expression((('-exp(-50*pow((x[0]-1), 2))', '0'),
                   ('0', '0')))
s0.assign(Function(S).interpolate(sic))

t = dt
temp = Function(U)
while t <= T + 1e-12:
   print "t = %f" % t
   
   # Solve for the velocity vector
   solver_u.solve()
   u0.assign(u1)
   
   # Solve for the stress tensor
   solver_s.solve()
   s0.assign(s1)
   
   # Move onto next timestep
   t += dt
   
   #G = inner(w, u)*dx - inner(w, u1-uexact)*dx
   #solve(lhs(G) == rhs(G), temp)

   output_u << u1
   #output_s << s1

