from eigenmode_2d import Eigenmode2DLF4
from eigenmode_3d import Eigenmode3DLF4
from pybench import Benchmark, parser
from pyop2.profiling import get_timers
from firedrake import *
import mpi4py
try:
    import pypapi
except:
    pypapi = None

parameters["pyop2_options"]["profiling"] = True
parameters["pyop2_options"]["lazy_evaluation"] = False

parameters["coffee"]["O2"] = True

class EigenmodeBench(Benchmark):
    warmups = 1
    repeats = 3

    method = 'eigenmode'
    benchmark = 'EigenmodeLF4'

    def eigenmode(self, dim=3, N=3, degree=1, dt=0.125, T=2.0,
                  explicit=True, opt=2):
        self.series['np'] = op2.MPI.comm.size
        self.series['dim'] = dim
        self.series['size'] = N
        self.series['T'] = T
        self.series['explicit'] = explicit
        self.series['opt'] = opt
        self.series['degree'] = degree

        # If dt is supressed (<0) Infer it based on Courant number
        if dt < 0:
            # Courant number of 0.5: (dx*C)/Vp
            dt = 0.5*(1.0/N)/(2.0**(degree-1))
        self.series['dt'] = dt

        parameters["coffee"]["O3"] = opt >= 3
        parameters["coffee"]["O4"] = opt >= 4

        try:
            wtime, ptime, flpins, mflops = pypapi.flops()
        except:
            wtime, ptime, flpins, mflops = (0., 0., 0, 0)
        if dim == 2:
            eigen = Eigenmode2DLF4(N, degree, dt, explicit=explicit, output=False)
            u1, s1 = eigen.eigenmode2d(T=T)
        elif dim == 3:
            eigen = Eigenmode3DLF4(N, degree, dt, explicit=explicit, output=False)
            u1, s1 = eigen.eigenmode3d(T=T)

        try:
            wtime, ptime, flpins, mflops = pypapi.flops()
        except:
            wtime, ptime, flpins, mflops = (0., 0., 0, 0)
        self.register_timing('PAPI::wtime', wtime)
        self.register_timing('PAPI::ptime', ptime)
        self.register_timing('PAPI::mflops', mflops)

        for task, timer in get_timers(reset=True).items():
            self.register_timing(task, timer.total)

        if explicit:
            petsc_events = {'Stress Solve' : ['MatMult', 'RHS Assembly'],
                            'Velocity Solve' : ['MatMult', 'RHS Assembly']}
        else:
            petsc_events = {'Stress Solve' : ['KSPSolve'],
                            'Velocity Solve' : ['KSPSolve']}

        for stage, events in petsc_events.items():
            for event in events:
                petsc_log = eigen.elastic.petsc_log
                info = petsc_log.Event(event).getPerfInfo(petsc_log.Stage(stage))
                flops = op2.MPI.comm.allreduce(info['flops'], op=mpi4py.MPI.SUM)
                time = op2.MPI.comm.allreduce(info['time'], op=mpi4py.MPI.MAX)
                mflops_s = flops / time / 1.e6 if time > 0. else 0.
                self.register_timing("%s::%s::Estimated Mflop/s" % (stage, event), mflops_s)

        self.meta['dofs'] = op2.MPI.comm.allreduce(eigen.elastic.S.dof_count, op=mpi4py.MPI.SUM)
        try:
            u_error, s_error = eigen.eigenmode_error(u1, s1)
            self.meta['u_error'] = u_error
            self.meta['s_error'] = s_error
        except RuntimeError:
            print "WARNING: Couldn't establish error norm"
            self.meta['u_error'] = 'NaN'
            self.meta['s_error'] = 'NaN'


if __name__ == '__main__':
    op2.init(log_level='ERROR')
    from ffc.log import set_level
    set_level('ERROR')

    EigenmodeBench(N=4, degree=1, dt=0.125).main()
