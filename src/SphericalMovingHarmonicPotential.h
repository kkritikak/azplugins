// Copyright (c) 2018-2020, Michael P. Howard
// Copyright (c) 2021-2024, Auburn University
// Part of azplugins, released under the BSD 3-Clause License.

/*!
 * \file SphericalMovingHarmonicPotential.h
 * \brief Declaration of SphericalMovingHarmonicPotential
 */

#ifndef AZPLUGINS_SPHERICAL_MOVING_HARMONIC_POTENTIAL_H_
#define AZPLUGINS_SPHERICAL_MOVING_HARMONIC_POTENTIAL_H_

#ifdef __HIPCC__
#error This header cannot be compiled by nvcc
#endif

#include "MovingHarmonicPotential.h"

#include <pybind11/pybind11.h>

namespace hoomd
    {

namespace azplugins
    {

//! Moving Harmonic Potential in a spherical (droplet) geometry
/*
 * The interface normal is that of a sphere, and its origin is (0,0,0).
 */
class PYBIND11_EXPORT SphericalMovingHarmonicPotential : public MovingHarmonicPotential
    {
    public:
    //! Constructor
    SphericalMovingHarmonicPotential(std::shared_ptr<SystemDefinition> sysdef,
                                     std::shared_ptr<Variant> interf);

    virtual ~SphericalMovingHarmonicPotential();

    protected:
    //! Implements the force calculation
    virtual void computeForces(unsigned int timestep);
    };

    } // end namespace azplugins

    } // end namespace hoomd
#endif // AZPLUGINS_SPHERICAL_MOVING_HARMONIC_POTENTIAL_H_
