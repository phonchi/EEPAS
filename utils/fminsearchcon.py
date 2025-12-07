#!/usr/bin/env python3
"""
fminsearchcon - Constrained Nelder-Mead optimization
Ported from MATLAB's fminsearchcon.m (John D'Errico)

Uses variable transformation to handle boundary constraints, uses penalty functions to handle linear and nonlinear inequality constraints.
"""

import numpy as np
from scipy.optimize import fmin


def fminsearchcon(fun, x0, lb=None, ub=None, A=None, b=None, nonlcon=None,
                  options=None, args=()):
    """
    Constrained Nelder-Mead optimization.

    Args:
        fun: Objective function f(x, \\*args)
        x0: Initial guess (array-like)
        lb: Lower bounds, can include -inf (optional)
        ub: Upper bounds, can include +inf (optional)
        A: Linear inequality constraint matrix A @ x <= b (optional)
        b: Linear inequality constraint RHS vector (optional)
        nonlcon: Nonlinear inequality constraint function, return <= 0 (optional)
        options: Optimization options dict (optional), containing:

            - maxiter: Maximum iterations (default: 200*n)
            - maxfun: Maximum function evaluations (default: 200*n)
            - xtol: Tolerance for x (default: 1e-4)
            - ftol: Tolerance for function value (default: 1e-4)
            - disp: Display progress (default: False)

        args: Additional arguments for objective and constraint functions (optional)

    Returns:
        tuple: (x, fval, exitflag, output) where:

            - x: Optimal solution (ndarray)
            - fval: Optimal function value (float)
            - exitflag: Exit flag (0=success, -1=failure)
            - output: Optimization information (dict)
    """
    # Convert to numpy array
    xsize = np.shape(x0)
    x0 = np.asarray(x0).flatten()
    n = len(x0)

    # Set default bounds
    if lb is None:
        lb = np.full(n, -np.inf)
    else:
        lb = np.asarray(lb).flatten()

    if ub is None:
        ub = np.full(n, np.inf)
    else:
        ub = np.asarray(ub).flatten()

    if len(lb) != n or len(ub) != n:
        raise ValueError('x0 is incompatible in size with either lb or ub')

    # Handle linear constraints
    if A is not None:
        A = np.asarray(A)
        b = np.asarray(b).flatten()
        if A.shape[0] != len(b):
            raise ValueError('Sizes of A and b are incompatible')
        if A.shape[1] != n:
            raise ValueError('A is incompatible in size with x0')
        # Check feasibility of initial point
        if np.any(A @ x0 > b):
            raise ValueError('Infeasible starting values (linear inequalities failed)')

    # Check nonlinear constraints
    if nonlcon is not None:
        cons = nonlcon(x0.reshape(xsize), *args)
        if np.any(cons > 0):
            raise ValueError('Infeasible starting values (nonlinear inequalities failed)')

    # Set default options
    if options is None:
        options = {}

    maxiter = options.get('maxiter', 200 * n)
    maxfun = options.get('maxfun', 200 * n)
    xtol = options.get('xtol', 1e-4)
    ftol = options.get('ftol', 1e-4)
    disp = options.get('disp', False)

    # Create parameter structure
    params = {
        'fun': fun,
        'args': args,
        'lb': lb,
        'ub': ub,
        'n': n,
        'xsize': xsize,
        'A': A,
        'b': b,
        'nonlcon': nonlcon
    }

    # Determine boundary type for each variable
    # 0: unconstrained, 1: lower bound only, 2: upper bound only, 3: both bounds, 4: fixed
    bound_class = np.zeros(n, dtype=int)
    for i in range(n):
        k = int(np.isfinite(lb[i])) + 2 * int(np.isfinite(ub[i]))
        if k == 3 and lb[i] == ub[i]:
            k = 4
        bound_class[i] = k

    params['bound_class'] = bound_class

    # Transform initial values to unconstrained space
    x0u = transform_forward(x0, params)

    # If all variables are fixed, return directly
    if len(x0u) == 0:
        x = x0
        fval = fun(x.reshape(xsize), *args)
        return x.reshape(xsize), fval, 0, {
            'iterations': 0,
            'funcCount': 1,
            'algorithm': 'fminsearch',
            'message': 'All variables were held fixed by the applied bounds'
        }

    # Call Nelder-Mead optimization (use fmin to match MATLAB fminsearch)
    result = fmin(
        lambda xu: intrafun(xu, params),
        x0u,
        maxiter=maxiter,
        maxfun=maxfun,
        xtol=xtol,
        ftol=ftol,
        disp=disp,
        full_output=True,
        retall=False
    )

    xu, fval, num_iter, num_funcalls, warnflag = result

    # Transform back to original space
    x = transform_backward(xu, params)

    # Organize output
    exitflag = 0 if warnflag == 0 else -1
    output = {
        'iterations': num_iter,
        'funcCount': num_funcalls,
        'algorithm': 'fminsearch',
        'message': 'Optimization terminated successfully' if exitflag == 0 else 'Maximum iterations/function calls exceeded'
    }

    return x.reshape(xsize), fval, exitflag, output


def transform_forward(x, params):
    """Transform constrained variables to unconstrained variables"""
    lb = params['lb']
    ub = params['ub']
    bound_class = params['bound_class']
    n = params['n']

    xu = []
    for i in range(n):
        bc = bound_class[i]
        if bc == 0:
            # Unconstrained
            xu.append(x[i])
        elif bc == 1:
            # Lower bound only: use square transformation
            if x[i] <= lb[i]:
                xu.append(0.0)
            else:
                xu.append(np.sqrt(x[i] - lb[i]))
        elif bc == 2:
            # Upper bound only: use square transformation
            if x[i] >= ub[i]:
                xu.append(0.0)
            else:
                xu.append(np.sqrt(ub[i] - x[i]))
        elif bc == 3:
            # Both bounds: use sin transformation
            if x[i] <= lb[i]:
                xu.append(-np.pi / 2)
            elif x[i] >= ub[i]:
                xu.append(np.pi / 2)
            else:
                # Normalize to [-1, 1]
                normalized = 2 * (x[i] - lb[i]) / (ub[i] - lb[i]) - 1
                # Transform to [2π-π/2, 2π+π/2] to avoid issues near 0
                xu.append(2 * np.pi + np.arcsin(np.clip(normalized, -1, 1)))
        # bc == 4 (fixed) variables not added to xu

    return np.array(xu)


def transform_backward(xu, params):
    """Transform unconstrained variables back to constrained variables"""
    lb = params['lb']
    ub = params['ub']
    bound_class = params['bound_class']
    n = params['n']

    x = np.zeros(n)
    k = 0  # xu index

    for i in range(n):
        bc = bound_class[i]
        if bc == 0:
            # Unconstrained
            x[i] = xu[k]
            k += 1
        elif bc == 1:
            # Lower bound only
            x[i] = lb[i] + xu[k]**2
            k += 1
        elif bc == 2:
            # Upper bound only
            x[i] = ub[i] - xu[k]**2
            k += 1
        elif bc == 3:
            # Both bounds
            xtrans = (np.sin(xu[k]) + 1) / 2
            x[i] = xtrans * (ub[i] - lb[i]) + lb[i]
            # Ensure within bounds (handle floating point errors)
            x[i] = np.clip(x[i], lb[i], ub[i])
            k += 1
        elif bc == 4:
            # Fixed variable
            x[i] = lb[i]

    return x


def intrafun(xu, params):
    """Internal objective function: transform variables and check constraints"""
    # Transform to original space
    x = transform_backward(xu, params)

    # Check linear constraints
    if params['A'] is not None:
        if np.any(params['A'] @ x > params['b']):
            return np.inf

    # Reshape to original shape
    x_shaped = x.reshape(params['xsize'])

    # Check nonlinear constraints
    if params['nonlcon'] is not None:
        cons = params['nonlcon'](x_shaped, *params['args'])
        if np.any(cons > 0):
            return np.inf

    # Evaluate objective function
    return params['fun'](x_shaped, *params['args'])
