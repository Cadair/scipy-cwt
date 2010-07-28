
__all__ = ['fixed_quad','quadrature','romberg','trapz','simps','romb',
           'cumtrapz','newton_cotes','composite']

from scipy.special.orthogonal import p_roots
from scipy.special import gammaln
from numpy import sum, ones, add, diff, isinf, isscalar, \
     asarray, real, trapz, arange, empty
import numpy as np
import math
import warnings

class AccuracyWarning(Warning):
    pass

def fixed_quad(func,a,b,args=(),n=5):
    """
    Compute a definite integral using fixed-order Gaussian quadrature.

    Integrate `func` from a to b using Gaussian quadrature of order n.

    Parameters
    ----------
    func : callable
        A Python function or method to integrate (must accept vector inputs).
    a : float
        Lower limit of integration.
    b : float
        Upper limit of integration.
    args : tuple, optional
        Extra arguments to pass to function, if any.
    n : int, optional
        Order of quadrature integration. Default is 5.

    Returns
    -------
    val : float
        Gaussian quadrature approximation to the integral

    See Also
    --------
    quad : adaptive quadrature using QUADPACK
    dblquad, tplquad : double and triple integrals
    romberg : adaptive Romberg quadrature
    quadrature : adaptive Gaussian quadrature
    romb, simps, trapz : integrators for sampled data
    cumtrapz : cumulative integration for sampled data
    ode, odeint - ODE integrators

    """
    [x,w] = p_roots(n)
    x = real(x)
    ainf, binf = map(isinf,(a,b))
    if ainf or binf:
        raise ValueError, "Gaussian quadrature is only available for " \
              "finite limits."
    y = (b-a)*(x+1)/2.0 + a
    return (b-a)/2.0*sum(w*func(y,*args),0), None

def vectorize1(func, args=(), vec_func=False):
    """Vectorize the call to a function.

    This is an internal utility function used by `romberg` and
    `quadrature` to create a vectorized version of a function.

    If `vec_func` is True, the function `func` is assumed to take vector
    arguments.

    Parameters
    ----------
    func : callable
        User defined function.
    args : tuple
        Extra arguments for the function.
    vec_func : bool
        True if the function func takes vector arguments.

    Returns
    -------
    vfunc : callable
        A function that will take a vector argument and return the
        result.

    """
    if vec_func:
        def vfunc(x):
            return func(x, *args)
    else:
        def vfunc(x):
            if isscalar(x):
                return func(x, *args)
            x = asarray(x)
            # call with first point to get output type
            y0 = func(x[0], *args)
            n = len(x)
            if hasattr(y0, 'dtype'):
                output = empty((n,), dtype=y0.dtype)
            else:
                output = empty((n,), dtype=type(y0))
            output[0] = y0
            for i in xrange(1, n):
                output[i] = func(x[i], *args)
            return output
    return vfunc

def quadrature(func, a, b, args=(), tol=1.49e-8, rtol=1.49e-8, maxiter=50,
               vec_func=True):
    """
    Compute a definite integral using fixed-tolerance Gaussian quadrature.

    Integrate func from a to b using Gaussian quadrature
    with absolute tolerance `tol`.

    Parameters
    ----------
    func : function
        A Python function or method to integrate.
    a : float
        Lower limit of integration.
    b : float
        Upper limit of integration.
    args : tuple, optional
        Extra arguments to pass to function.
    tol, rol : float, optional
        Iteration stops when error between last two iterates is less than
        `tol` OR the relative change is less than `rtol`.
    maxiter : int, optional
        Maximum number of iterations.
    vec_func : bool, optional
        True or False if func handles arrays as arguments (is
        a "vector" function). Default is True.

    Returns
    -------
    val : float
        Gaussian quadrature approximation (within tolerance) to integral.
    err : float
        Difference between last two estimates of the integral.

    See also
    --------
    romberg: adaptive Romberg quadrature
    fixed_quad: fixed-order Gaussian quadrature
    quad: adaptive quadrature using QUADPACK
    dblquad: double integrals
    tplquad: triple integrals
    romb: integrator for sampled data
    simps: integrator for sampled data
    trapz: integrator for sampled data
    cumtrapz: cumulative integration for sampled data
    ode: ODE integrator
    odeint: ODE integrator

    """
    vfunc = vectorize1(func, args, vec_func=vec_func)
    val = np.inf
    err = np.inf
    for n in xrange(1, maxiter+1):
        newval = fixed_quad(vfunc, a, b, (), n)[0]
        err = abs(newval-val)
        val = newval

        if err < tol or err < rtol*abs(val):
            break
    else:
        warnings.warn(
            "maxiter (%d) exceeded. Latest difference = %e" % (maxiter, err),
            AccuracyWarning)
    return val, err

def tupleset(t, i, value):
    l = list(t)
    l[i] = value
    return tuple(l)

def cumtrapz(y, x=None, dx=1.0, axis=-1):
    """
    Cumulatively integrate y(x) using samples along the given axis
    and the composite trapezoidal rule.  If x is None, spacing given by dx
    is assumed.

    Parameters
    ----------
    y : array

    x : array, optional

    dx : int, optional

    axis : int, optional
        Specifies the axis to cumulate:

          - -1 --> X axis
          - 0  --> Z axis
          - 1  --> Y axis

    See Also
    --------

      quad: adaptive quadrature using QUADPACK
      romberg: adaptive Romberg quadrature
      quadrature: adaptive Gaussian quadrature
      fixed_quad: fixed-order Gaussian quadrature
      dblquad: double integrals
      tplquad: triple integrals
      romb: integrators for sampled data
      trapz: integrators for sampled data
      cumtrapz: cumulative integration for sampled data
      ode: ODE integrators
      odeint: ODE integrators

    """
    y = asarray(y)
    if x is None:
        d = dx
    else:
        d = diff(x,axis=axis)
    nd = len(y.shape)
    slice1 = tupleset((slice(None),)*nd, axis, slice(1, None))
    slice2 = tupleset((slice(None),)*nd, axis, slice(None, -1))
    return add.accumulate(d * (y[slice1]+y[slice2])/2.0,axis)

def _basic_simps(y,start,stop,x,dx,axis):
    nd = len(y.shape)
    if start is None:
        start = 0
    step = 2
    all = (slice(None),)*nd
    slice0 = tupleset(all, axis, slice(start, stop, step))
    slice1 = tupleset(all, axis, slice(start+1, stop+1, step))
    slice2 = tupleset(all, axis, slice(start+2, stop+2, step))

    if x is None:  # Even spaced Simpson's rule.
        result = add.reduce(dx/3.0* (y[slice0]+4*y[slice1]+y[slice2]),
                                    axis)
    else:
        # Account for possibly different spacings.
        #    Simpson's rule changes a bit.
        h = diff(x,axis=axis)
        sl0 = tupleset(all, axis, slice(start, stop, step))
        sl1 = tupleset(all, axis, slice(start+1, stop+1, step))
        h0 = h[sl0]
        h1 = h[sl1]
        hsum = h0 + h1
        hprod = h0 * h1
        h0divh1 = h0 / h1
        result = add.reduce(hsum/6.0*(y[slice0]*(2-1.0/h0divh1) + \
                                              y[slice1]*hsum*hsum/hprod + \
                                              y[slice2]*(2-h0divh1)),axis)
    return result


def simps(y, x=None, dx=1, axis=-1, even='avg'):
    """
    Integrate y(x) using samples along the given axis and the composite
    Simpson's rule.  If x is None, spacing of dx is assumed.

    If there are an even number of samples, N, then there are an odd
    number of intervals (N-1), but Simpson's rule requires an even number
    of intervals.  The parameter 'even' controls how this is handled.

    Parameters
    ----------
    y : array_like
        Array to be integrated.
    x : array_like, optional
        If given, the points at which `y` is sampled.
    dx : int, optional
        Spacing of integration points along axis of `y`. Only used when
        `x` is None. Default is 1.
    axis : int, optional
        Axis along which to integrate. Default is the last axis.
    even : {'avg', 'first', 'str'}, optional
        'avg' : Average two results:1) use the first N-2 intervals with
                  a trapezoidal rule on the last interval and 2) use the last
                  N-2 intervals with a trapezoidal rule on the first interval.

        'first' : Use Simpson's rule for the first N-2 intervals with
                a trapezoidal rule on the last interval.

        'last' : Use Simpson's rule for the last N-2 intervals with a
               trapezoidal rule on the first interval.

    See Also
    --------
    quad: adaptive quadrature using QUADPACK
    romberg: adaptive Romberg quadrature
    quadrature: adaptive Gaussian quadrature
    fixed_quad: fixed-order Gaussian quadrature
    dblquad: double integrals
    tplquad: triple integrals
    romb: integrators for sampled data
    trapz: integrators for sampled data
    cumtrapz: cumulative integration for sampled data
    ode: ODE integrators
    odeint: ODE integrators

    Notes
    -----
    For an odd number of samples that are equally spaced the result is
    exact if the function is a polynomial of order 3 or less.  If
    the samples are not equally spaced, then the result is exact only
    if the function is a polynomial of order 2 or less.

    """
    y = asarray(y)
    nd = len(y.shape)
    N = y.shape[axis]
    last_dx = dx
    first_dx = dx
    returnshape = 0
    if not x is None:
        x = asarray(x)
        if len(x.shape) == 1:
            shapex = ones(nd)
            shapex[axis] = x.shape[0]
            saveshape = x.shape
            returnshape = 1
            x=x.reshape(tuple(shapex))
        elif len(x.shape) != len(y.shape):
            raise ValueError, "If given, shape of x must be 1-d or the " \
                  "same as y."
        if x.shape[axis] != N:
            raise ValueError, "If given, length of x along axis must be the " \
                  "same as y."
    if N % 2 == 0:
        val = 0.0
        result = 0.0
        slice1 = (slice(None),)*nd
        slice2 = (slice(None),)*nd
        if not even in ['avg', 'last', 'first']:
            raise ValueError, \
                  "Parameter 'even' must be 'avg', 'last', or 'first'."
        # Compute using Simpson's rule on first intervals
        if even in ['avg', 'first']:
            slice1 = tupleset(slice1, axis, -1)
            slice2 = tupleset(slice2, axis, -2)
            if not x is None:
                last_dx = x[slice1] - x[slice2]
            val += 0.5*last_dx*(y[slice1]+y[slice2])
            result = _basic_simps(y,0,N-3,x,dx,axis)
        # Compute using Simpson's rule on last set of intervals
        if even in ['avg', 'last']:
            slice1 = tupleset(slice1, axis, 0)
            slice2 = tupleset(slice2, axis, 1)
            if not x is None:
                first_dx = x[tuple(slice2)] - x[tuple(slice1)]
            val += 0.5*first_dx*(y[slice2]+y[slice1])
            result += _basic_simps(y,1,N-2,x,dx,axis)
        if even == 'avg':
            val /= 2.0
            result /= 2.0
        result = result + val
    else:
        result = _basic_simps(y,0,N-2,x,dx,axis)
    if returnshape:
        x = x.reshape(saveshape)
    return result

def romb(y, dx=1.0, axis=-1, show=False):
    """
    Romberg integration using samples of a function

    Parameters
    -----------
      y : array like
           a vector of 2**k + 1 equally-spaced samples of a function

      dx : array like
           the sample spacing.

      axis : array like?
           the axis along which to integrate

      show : Boolean
           When y is a single 1-d array, then if this argument is True
           print the table showing Richardson extrapolation from the
           samples.

    Returns
    -----------

       ret : array_like?
          The integrated result for each axis.

    See also:

      quad - adaptive quadrature using QUADPACK
      romberg - adaptive Romberg quadrature
      quadrature - adaptive Gaussian quadrature
      fixed_quad - fixed-order Gaussian quadrature
      dblquad, tplquad - double and triple integrals
      simps, trapz - integrators for sampled data
      cumtrapz - cumulative integration for sampled data
      ode, odeint - ODE integrators

    """
    y = asarray(y)
    nd = len(y.shape)
    Nsamps = y.shape[axis]
    Ninterv = Nsamps-1
    n = 1
    k = 0
    while n < Ninterv:
        n <<= 1
        k += 1
    if n != Ninterv:
        raise ValueError, \
              "Number of samples must be one plus a non-negative power of 2."

    R = {}
    all = (slice(None),) * nd
    slice0 = tupleset(all, axis, 0)
    slicem1 = tupleset(all, axis, -1)
    h = Ninterv*asarray(dx)*1.0
    R[(1,1)] = (y[slice0] + y[slicem1])/2.0*h
    slice_R = all
    start = stop = step = Ninterv
    for i in range(2,k+1):
        start >>= 1
        slice_R = tupleset(slice_R, axis, slice(start,stop,step))
        step >>= 1
        R[(i,1)] = 0.5*(R[(i-1,1)] + h*add.reduce(y[slice_R],axis))
        for j in range(2,i+1):
            R[(i,j)] = R[(i,j-1)] + \
                       (R[(i,j-1)]-R[(i-1,j-1)]) / ((1 << (2*(j-1)))-1)
        h = h / 2.0

    if show:
        if not isscalar(R[(1,1)]):
            print "*** Printing table only supported for integrals" + \
                  " of a single data set."
        else:
            try:
                precis = show[0]
            except (TypeError, IndexError):
                precis = 5
            try:
                width = show[1]
            except (TypeError, IndexError):
                width = 8
            formstr = "%" + str(width) + '.' + str(precis)+'f'

            print "\n       Richardson Extrapolation Table for Romberg Integration       "
            print "===================================================================="
            for i in range(1,k+1):
                for j in range(1,i+1):
                    print formstr % R[(i,j)],
                print
            print "====================================================================\n"

    return R[(k,k)]



# Romberg quadratures for numeric integration.
#
# Written by Scott M. Ransom <ransom@cfa.harvard.edu>
# last revision: 14 Nov 98
#
# Cosmetic changes by Konrad Hinsen <hinsen@cnrs-orleans.fr>
# last revision: 1999-7-21
#
# Adapted to scipy by Travis Oliphant <oliphant.travis@ieee.org>
# last revision: Dec 2001

def _difftrap(function, interval, numtraps):
    """
    Perform part of the trapezoidal rule to integrate a function.
    Assume that we had called difftrap with all lower powers-of-2
    starting with 1.  Calling difftrap only returns the summation
    of the new ordinates.  It does _not_ multiply by the width
    of the trapezoids.  This must be performed by the caller.
        'function' is the function to evaluate (must accept vector arguments).
        'interval' is a sequence with lower and upper limits
                   of integration.
        'numtraps' is the number of trapezoids to use (must be a
                   power-of-2).
    """
    if numtraps <= 0:
        raise ValueError("numtraps must be > 0 in difftrap().")
    elif numtraps == 1:
        return 0.5*(function(interval[0])+function(interval[1]))
    else:
        numtosum = numtraps/2
        h = float(interval[1]-interval[0])/numtosum
        lox = interval[0] + 0.5 * h;
        points = lox + h * arange(0, numtosum)
        s = sum(function(points),0)
        return s

def _romberg_diff(b, c, k):
    """
    Compute the differences for the Romberg quadrature corrections.
    See Forman Acton's "Real Computing Made Real," p 143.
    """
    tmp = 4.0**k
    return (tmp * c - b)/(tmp - 1.0)

def _printresmat(function, interval, resmat):
    # Print the Romberg result matrix.
    i = j = 0
    print 'Romberg integration of', `function`,
    print 'from', interval
    print ''
    print '%6s %9s %9s' % ('Steps', 'StepSize', 'Results')
    for i in range(len(resmat)):
        print '%6d %9f' % (2**i, (interval[1]-interval[0])/(2.**i)),
        for j in range(i+1):
            print '%9f' % (resmat[i][j]),
        print ''
    print ''
    print 'The final result is', resmat[i][j],
    print 'after', 2**(len(resmat)-1)+1, 'function evaluations.'

def romberg(function, a, b, args=(), tol=1.48E-8, show=False,
            divmax=10, vec_func=False):
    """
    Romberg integration of a callable function or method.

    Returns the integral of `function` (a function of one variable)
    over the interval (`a`, `b`).

    If `show` is 1, the triangular array of the intermediate results
    will be printed.  If `vec_func` is True (default is False), then `function` is
    assumed to support vector arguments.

    Parameters
    ----------
    function : callable
        Function to be integrated.
    a : float
        Lower limit of integration.
    b : float
        Upper limit of integration.

    Returns
    --------
    results  : float
        Result of the integration.

    Other Parameters
    ----------------
    args : tuple, optional
        Extra arguments to pass to function. Each element of `args` will
        be passed as a single argument to `func`. Default is to pass no
        extra arguments.
    tol : float, optional
        The desired tolerance. Default is 1.48e-8.
    show : bool, optional
        Whether to print the results. Default is False.
    divmax : int, optional
        ?? Default is 10.
    vec_func : bool, optional
        Whether `func` handles arrays as arguments (i.e whether it is a
        "vector" function). Default is False.

    See Also
    --------
    fixed_quad : Fixed-order Gaussian quadrature.
    quad : Adaptive quadrature using QUADPACK.
    dblquad, tplquad : Double and triple integrals.
    romb, simps, trapz : Integrators for sampled data.
    cumtrapz : Cumulative integration for sampled data.
    ode, odeint : ODE integrators.

    References
    ----------
    .. [1] 'Romberg's method' http://en.wikipedia.org/wiki/Romberg%27s_method

    Examples
    --------
    Integrate a gaussian from 0,1 and compare to the error function.

    >>> from scipy.special import erf
    >>> gaussian = lambda x: 1/np.sqrt(np.pi) * np.exp(-x**2)
    >>> result = romberg(gaussian, 0, 1, show=True)
    Romberg integration of <function vfunc at 0x101eceaa0> from [0, 1]

    ::

       Steps  StepSize  Results
           1  1.000000  0.385872
           2  0.500000  0.412631  0.421551
           4  0.250000  0.419184  0.421368  0.421356
           8  0.125000  0.420810  0.421352  0.421350  0.421350
          16  0.062500  0.421215  0.421350  0.421350  0.421350  0.421350
          32  0.031250  0.421317  0.421350  0.421350  0.421350  0.421350  0.421350

    The final result is 0.421350396475 after 33 function evaluations.

    >>> print 2*result,erf(1)
    0.84270079295 0.84270079295

    """
    if isinf(a) or isinf(b):
        raise ValueError("Romberg integration only available for finite limits.")
    vfunc = vectorize1(function, args, vec_func=vec_func)
    i = n = 1
    interval = [a,b]
    intrange = b-a
    ordsum = _difftrap(vfunc, interval, n)
    result = intrange * ordsum
    resmat = [[result]]
    lastresult = result + tol * 2.0
    while (abs(result - lastresult) > tol) and (i <= divmax):
        n = n * 2
        ordsum = ordsum + _difftrap(vfunc, interval, n)
        resmat.append([])
        resmat[i].append(intrange * ordsum / n)
        for k in range(i):
            resmat[i].append(_romberg_diff(resmat[i-1][k], resmat[i][k], k+1))
        result = resmat[i][i]
        lastresult = resmat[i-1][i-1]
        i = i + 1
    if show:
        _printresmat(vfunc, interval, resmat)
    return result


# Coefficients for Netwon-Cotes quadrature
#
# These are the points being used
#  to construct the local interpolating polynomial
#  a are the weights for Newton-Cotes integration
#  B is the error coefficient.
#  error in these coefficients grows as N gets larger.
#  or as samples are closer and closer together

# You can use maxima to find these rational coefficients
#  for equally spaced data using the commands
#  a(i,N) := integrate(product(r-j,j,0,i-1) * product(r-j,j,i+1,N),r,0,N) / ((N-i)! * i!) * (-1)^(N-i);
#  Be(N) := N^(N+2)/(N+2)! * (N/(N+3) - sum((i/N)^(N+2)*a(i,N),i,0,N));
#  Bo(N) := N^(N+1)/(N+1)! * (N/(N+2) - sum((i/N)^(N+1)*a(i,N),i,0,N));
#  B(N) := (if (mod(N,2)=0) then Be(N) else Bo(N));
#
# pre-computed for equally-spaced weights
#
# num_a, den_a, int_a, num_B, den_B = _builtincoeffs[N]
#
#  a = num_a*array(int_a)/den_a
#  B = num_B*1.0 / den_B
#
#  integrate(f(x),x,x_0,x_N) = dx*sum(a*f(x_i)) + B*(dx)^(2k+3) f^(2k+2)(x*)
#    where k = N // 2
#
_builtincoeffs = {
    1:(1,2,[1,1],-1,12),
    2:(1,3,[1,4,1],-1,90),
    3:(3,8,[1,3,3,1],-3,80),
    4:(2,45,[7,32,12,32,7],-8,945),
    5:(5,288,[19,75,50,50,75,19],-275,12096),
    6:(1,140,[41,216,27,272,27,216,41],-9,1400),
    7:(7,17280,[751,3577,1323,2989,2989,1323,3577,751],-8183,518400),
    8:(4,14175,[989,5888,-928,10496,-4540,10496,-928,5888,989],
       -2368,467775),
    9:(9,89600,[2857,15741,1080,19344,5778,5778,19344,1080,
                15741,2857], -4671, 394240),
    10:(5,299376,[16067,106300,-48525,272400,-260550,427368,
                  -260550,272400,-48525,106300,16067],
        -673175, 163459296),
    11:(11,87091200,[2171465,13486539,-3237113, 25226685,-9595542,
                     15493566,15493566,-9595542,25226685,-3237113,
                     13486539,2171465], -2224234463, 237758976000),
    12:(1, 5255250, [1364651,9903168,-7587864,35725120,-51491295,
                     87516288,-87797136,87516288,-51491295,35725120,
                     -7587864,9903168,1364651], -3012, 875875),
    13:(13, 402361344000,[8181904909, 56280729661, -31268252574,
                          156074417954,-151659573325,206683437987,
                          -43111992612,-43111992612,206683437987,
                          -151659573325,156074417954,-31268252574,
                          56280729661,8181904909], -2639651053,
        344881152000),
    14:(7, 2501928000, [90241897,710986864,-770720657,3501442784,
                        -6625093363,12630121616,-16802270373,19534438464,
                        -16802270373,12630121616,-6625093363,3501442784,
                        -770720657,710986864,90241897], -3740727473,
        1275983280000)
    }

def newton_cotes(rn,equal=0):
    """
    Return weights and error coefficient for Newton-Cotes integration.

    Suppose we have (N+1) samples of f at the positions
    x_0, x_1, ..., x_N.  Then an N-point Newton-Cotes formula for the
    integral between x_0 and x_N is:

    :math:`\\int_{x_0}^{x_N} f(x)dx = \\Delta x \\sum_{i=0}^{N} a_i f(x_i)
    + B_N (\\Delta x)^{N+2} f^{N+1} (\\xi)`

    where :math:`\\xi \\in [x_0,x_N]` and :math:`\\Delta x = \\frac{x_N-x_0}{N}`
    is the averages samples spacing.

    If the samples are equally-spaced and N is even, then the error
    term is :math:`B_N (\\Delta x)^{N+3} f^{N+2}(\\xi)`.

    Parameters
    ----------

    rn : int
        The integer order for equally-spaced data
        or the relative positions of the samples with
        the first sample at 0 and the last at N, where
        N+1 is the length of rn.  N is the order of the Newton
    equal: int, optional
        Set to 1 to enforce equally spaced data

    Returns
    -------
    an : array
        1-d array of weights to apply to the function at
        the provided sample positions.
    B  : float
        error coefficient

    Notes
    -----
    Normally, the Newton-Cotes rules are used on smaller integration
    regions and a composite rule is used to return the total integral.

    """
    try:
        N = len(rn)-1
        if equal:
            rn = np.arange(N+1)
        elif np.all(np.diff(rn)==1):
            equal = 1
    except:
        N = rn
        rn = np.arange(N+1)
        equal = 1

    if equal and N in _builtincoeffs:
        na, da, vi, nb, db = _builtincoeffs[N]
        return na*np.array(vi,float)/da, float(nb)/db

    if (rn[0] != 0) or (rn[-1] != N):
        raise ValueError, "The sample positions must start at 0"\
              " and end at N"
    yi = rn / float(N)
    ti = 2.0*yi - 1
    nvec = np.arange(0,N+1)
    C = np.mat(ti**nvec[:,np.newaxis])
    Cinv = C.I
    # improve precision of result
    Cinv = 2*Cinv - Cinv*C*Cinv
    Cinv = 2*Cinv - Cinv*C*Cinv
    Cinv = Cinv.A
    vec = 2.0/ (nvec[::2]+1)
    ai = np.dot(Cinv[:,::2],vec) * N/2

    if (N%2 == 0) and equal:
        BN = N/(N+3.)
        power = N+2
    else:
        BN = N/(N+2.)
        power = N+1

    BN = BN - np.dot(yi**power, ai)
    p1 = power+1
    fac = power*math.log(N) - gammaln(p1)
    fac = math.exp(fac)
    return ai, BN*fac


# Should only use if samples are forced on you
def composite(f,x=None,dx=1,axis=-1,n=5):
    pass
