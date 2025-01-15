# Copyright (c) 2018-2020, Michael P. Howard
# Copyright (c) 2021-2024, Auburn University
# Part of azplugins, released under the BSD 3-Clause License.

import hoomd
from hoomd.azplugins import external
import pytest
import numpy


class CustomVariant(hoomd.variant.Variant):
    def __init__(self, z):
        hoomd.variant.Variant.__init__(self)
        self.z = z

    def __call__(self, timestep):
        if timestep <= 1:
            z = self.z
        else:
            z = self.z - 1
        return z

    def _min(self):
        return self.z - 1

    def _max(self):
        return float(self.z)


@pytest.fixture
def custom_variant_fixture():
    return CustomVariant(z=5.0)


@pytest.fixture
def integrator():
    ig = hoomd.md.Integrator(dt=0.0)
    nve = hoomd.md.methods.ConstantVolume(hoomd.filter.All())
    ig.methods = [nve]
    return ig


@pytest.fixture
def snap():
    snap_ = hoomd.Snapshot()
    if snap_.communicator.rank == 0:
        snap_.configuration.box = [20, 20, 20, 0, 0, 0]
        snap_.particles.N = 4
        snap_.particles.types = ["A", "B"]
        snap_.particles.position[:] = [
            [0, 0, 4.6],
            [0, 0, -5.4],
            [0, 5.6, 0],
            [6.6, 0, 0],
        ]
        snap_.particles.velocity[:] = [[0, 0, 0]] * 4
        snap_.particles.typeid[:] = [0, 1, 0, 0]
    return snap_


@pytest.mark.parametrize("cls", [external.SphericalHarmonicBarrier], ids=["Spherical"])
def test_spherical_harmonic_barrier(
    simulation_factory, cls, integrator, snap, custom_variant_fixture
):
    sim = simulation_factory(snap)
    sim.operations.integrator = integrator

    barrier = cls(interface=custom_variant_fixture)
    kA = 50.0
    dB = 2.0
    kB = kA * dB**2

    barrier.params["A"] = dict(k=kA, offset=0.1)
    barrier.params["B"] = dict(k=kB, offset=-0.1)

    sim.operations.add(barrier)
    #  at first step the interface will not move
    sim.run(1)

    # Test forces on particles
    forces = barrier.forces
    energies = barrier.energies
    # particle 0 is outside interaction range
    assert numpy.isclose(energies[0], 0.0)
    assert numpy.isclose(forces[0][0], 0.0, atol=1e-4)
    assert numpy.isclose(forces[0][1], 0.0, atol=1e-4)
    assert numpy.isclose(forces[0][2], 0.0, atol=1e-4)
    # particle 1 (type B) is experiencing the harmonic potential in +z
    assert numpy.isclose(energies[1], 0.5 * kB * 0.5**2, atol=1e-4)
    assert numpy.isclose(forces[1][0], 0.0, atol=1e-4)
    assert numpy.isclose(forces[1][1], 0.0, atol=1e-4)
    assert numpy.isclose(forces[1][2], kB * 0.5, atol=1e-4)
    # particle 2 (type A) is also experiencing the harmonic potential but in -y
    assert numpy.isclose(energies[2], 0.5 * kA * 0.5**2, atol=1e-4)
    assert numpy.isclose(forces[2][0], 0.0, atol=1e-4)
    assert numpy.isclose(forces[2][1], -kA * 0.5, atol=1e-4)
    assert numpy.isclose(forces[2][2], 0.0, atol=1e-4)
    # particle 3 (type A) is experiencing force in -x
    assert numpy.isclose(energies[3], 0.5 * kA * 1.5**2, atol=1e-4)
    assert numpy.isclose(forces[3][0], -kA * 1.5, atol=1e-4)
    assert numpy.isclose(forces[3][1], 0.0, atol=1e-4)
    assert numpy.isclose(forces[3][2], 0.0, atol=1e-4)

    # disable B interactions for the next test
    barrier.params["B"] = dict(k=0.0, offset=-0.1)
    # advance the simulation two steps so that now the interface is at 4.0
    # in both verlet steps
    sim.run(2)

    forces = barrier.forces
    energies = barrier.energies
    # particle 0 is now inside the harmonic region, -x
    assert numpy.isclose(energies[0], 0.5 * kA * 0.5**2)
    assert numpy.isclose(forces[0][0], 0.0, atol=1e-4)
    assert numpy.isclose(forces[0][1], 0.0, atol=1e-4)
    assert numpy.isclose(forces[0][2], -kA * 0.5, atol=1e-4)
    # particle 1 (type B) should now be ignored because of the K
    assert numpy.isclose(energies[1], 0.0, atol=1e-4)
    assert numpy.isclose(forces[1][0], 0.0, atol=1e-4)
    assert numpy.isclose(forces[1][1], 0.0, atol=1e-4)
    assert numpy.isclose(forces[1][2], 0.0, atol=1e-4)
    # particle 2 (type A) is 1.5 distance away from the interface now
    assert numpy.isclose(energies[2], 0.5 * kA * 1.5**2, atol=1e-4)
    assert numpy.isclose(forces[2][0], 0.0, atol=1e-4)
    assert numpy.isclose(forces[2][1], -kA * 1.5, atol=1e-4)
    assert numpy.isclose(forces[2][2], 0.0, atol=1e-4)
    # particle 3 (type A) is still experiencing force in -x but with larger strength
    assert numpy.isclose(energies[3], 0.5 * kA * 2.5**2, atol=1e-4)
    assert numpy.isclose(forces[3][0], -kA * 2.5, atol=1e-4)
    assert numpy.isclose(forces[3][1], 0.0, atol=1e-4)
    assert numpy.isclose(forces[3][2], 0.0, atol=1e-4)


@pytest.mark.parametrize("cls", [external.PlanarHarmonicBarrier], ids=["Planar"])
def test_planar_harmonic_barrier(
    simulation_factory, cls, integrator, custom_variant_fixture
):
    snap = hoomd.Snapshot()
    if snap.communicator.rank == 0:
        snap.configuration.box = [20, 20, 20, 0, 0, 0]
        snap.particles.N = 4
        snap.particles.types = ["A", "B"]
        snap.particles.position[:] = [
            [1, 1, 4.6],
            [-1, 1, 5.4],
            [1, -1, 5.6],
            [-1, -1, 6.6],
        ]
        snap.particles.velocity[:] = [[0, 0, 0]] * 4
        snap.particles.typeid[:] = [0, 1, 0, 0]
    sim = simulation_factory(snap)
    sim.operations.integrator = integrator

    barrier = cls(interface=custom_variant_fixture)
    kA = 50.0
    dB = 2.0
    kB = kA * dB**2

    barrier.params["A"] = dict(k=kA, offset=0.1)
    barrier.params["B"] = dict(k=kB, offset=-0.1)

    sim.operations.add(barrier)
    #  at first step the interface will not move
    sim.run(1)

    # Test forces on particles
    forces = barrier.forces
    energies = barrier.energies
    # particle 0 is outside interaction range
    assert numpy.isclose(energies[0], 0.0)
    assert numpy.isclose(forces[0][0], 0.0, atol=1e-4)
    assert numpy.isclose(forces[0][1], 0.0, atol=1e-4)
    assert numpy.isclose(forces[0][2], 0.0, atol=1e-4)
    # particle 1 (type B) is experiencing the harmonic potential
    assert numpy.isclose(energies[1], 0.5 * kB * 0.5**2, atol=1e-4)
    assert numpy.isclose(forces[1][0], 0.0, atol=1e-4)
    assert numpy.isclose(forces[1][1], 0.0, atol=1e-4)
    assert numpy.isclose(forces[1][2], -kB * 0.5, atol=1e-4)
    # particle 2 (type A) is also experiencing the harmonic potential
    assert numpy.isclose(energies[2], 0.5 * kA * 0.5**2, atol=1e-4)
    assert numpy.isclose(forces[2][0], 0.0, atol=1e-4)
    assert numpy.isclose(forces[2][1], 0.0, atol=1e-4)
    assert numpy.isclose(forces[2][2], -kA * 0.5, atol=1e-4)
    # particle 3 (type A) is experiencing the harmonic potential
    assert numpy.isclose(energies[3], 0.5 * kA * 1.5**2, atol=1e-4)
    assert numpy.isclose(forces[3][0], 0.0, atol=1e-4)
    assert numpy.isclose(forces[3][1], 0.0, atol=1e-4)
    assert numpy.isclose(forces[3][2], -kA * 1.5, atol=1e-4)

    # disable B interactions for the next test
    barrier.params["B"] = dict(k=0.0, offset=-0.1)
    # advance the simulation two steps so that now the interface is at 4.0
    # in both verlet steps
    sim.run(2)

    forces = barrier.forces
    energies = barrier.energies
    # particle 0 is now inside the harmonic region, -x
    assert numpy.isclose(energies[0], 0.5 * kA * 0.5**2, atol=1e-4)
    assert numpy.isclose(forces[0][0], 0.0, atol=1e-4)
    assert numpy.isclose(forces[0][1], 0.0, atol=1e-4)
    assert numpy.isclose(forces[0][2], -kA * 0.5, atol=1e-4)
    # particle 1 (type B) should now be ignored because of the K
    assert numpy.isclose(energies[1], 0.0, atol=1e-4)
    assert numpy.isclose(forces[1][0], 0.0, atol=1e-4)
    assert numpy.isclose(forces[1][1], 0.0, atol=1e-4)
    assert numpy.isclose(forces[1][2], 0.0, atol=1e-4)
    # particle 2 (type A) is 1.5 distance away from the interface now
    assert numpy.isclose(energies[2], 0.5 * kA * 1.5**2, atol=1e-4)
    assert numpy.isclose(forces[2][0], 0.0, atol=1e-4)
    assert numpy.isclose(forces[2][1], 0.0, atol=1e-4)
    assert numpy.isclose(forces[2][2], -kA * 1.5, atol=1e-4)
    # particle 3 (type A) is still experiencing force in -x but with larger strength
    assert numpy.isclose(energies[3], 0.5 * kA * 2.5**2, atol=1e-4)
    assert numpy.isclose(forces[3][0], 0.0, atol=1e-4)
    assert numpy.isclose(forces[3][1], 0.0, atol=1e-4)
    assert numpy.isclose(forces[3][2], -kA * 2.5, atol=1e-4)