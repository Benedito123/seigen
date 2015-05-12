#!/usr/bin/env python

from dolfin import *
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

mesh = UnitSquareMesh(20, 20)

S = TensorFunctionSpace(mesh, "CG", 2)
U = VectorFunctionSpace(mesh, "CG", 1)
dimension = len(U.split())

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
T = 5.0
dt = 0.005
mu = 0.25
l = 0.5

Vp = sqrt((l + 2*mu)/density) # P-wave velocity
Vs = sqrt(mu/density) # S-wave velocity


# Weak forms
F_u = density*inner(w, (u - u0)/dt)*dx + inner(grad(w), s0)*dx
F_s = inner(v, (s - s0)/dt)*dx - inner(v, l*(div(u0))*Identity(dimension))*dx - inner(v, mu*(grad(u0) + grad(u0).T))*dx

problem_u = LinearVariationalProblem(lhs(F_u), rhs(F_u), u1)
solver_u = LinearVariationalSolver(problem_u)

problem_s = LinearVariationalProblem(lhs(F_s), rhs(F_s), s1)
solver_s = LinearVariationalSolver(problem_s)

output_u = File("velocity.pvd")
output_s = File("stress.pvd")

# Initial conditions
a = sqrt(2)*pi*Vs
b = 2*pi*mu
uic = Expression(('a*cos(pi*x[0])*sin(pi*x[1])*cos(a*t)','-a*sin(pi*x[0])*cos(pi*x[1])*cos(a*t)'), a=a, t=0)
u0.assign(uic)
sic = Expression((('-b*sin(pi*x[0])*sin(pi*x[1])*sin(a*t)','0'),
                   ('0','b*sin(pi*x[0])*sin(pi*x[1])*sin(a*t)')), a=a, b=b, t=dt/2.0)
s0.assign(sic)

t = dt
while t < T:
   print "t = %f" % t
   
   # Solve for the velocity vector
   solver_u.solve()
   u0.assign(u1)
   
   # Solve for the stress tensor
   solver_s.solve()
   s0.assign(s1)
   
   # Move onto next timestep
   t += dt
   
   output_u << u1
   output_s << s1
