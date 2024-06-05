// Copyright (c) 2018-2020, Michael P. Howard
// Copyright (c) 2021-2024, Auburn University
// Part of azplugins, released under the BSD 3-Clause License.

#ifndef AZPLUGINS_CONSTANT_FLOW_H_
#define AZPLUGINS_CONSTANT_FLOW_H_

#ifndef __HIPCC__
#include <pybind11/pybind11.h>
#endif

#include "hoomd/HOOMDMath.h"

#ifndef __HIPCC__
#define HOSTDEVICE __host__ __device__
#else
#define HOSTDEVICE
#endif // __HIPCC__

namespace hoomd
    {
namespace azplugins
    {

//! Position-independent flow along a vector
class ConstantFlow
    {
    public:
    //! Constructor
    /*!
     *\param U_ Flow field
     */
    ConstantFlow(Scalar3 U_) : U(U_) { }
    //! Evaluate the flow field
    /*!
     * \param r position to evaluate flow
     *
     * This is just a constant, independent of \a r.
     */
    HOSTDEVICE Scalar3 operator()(const Scalar3& r) const
        {
        return U;
        }

    HOSTDEVICE Scalar3 getVelocity() const
        {
        return U;
        }

    HOSTDEVICE void setVelocity(const Scalar3& U_)
        {
        U = U_;
        }

    private:
    Scalar3 U; //!< Flow field
    };

    } // namespace azplugins
    } // namespace hoomd

#undef HOSTDEVICE

#endif // AZPLUGINS_CONSTANT_FLOW_H_
