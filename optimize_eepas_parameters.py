#!/usr/bin/env python3
"""
EEPAS Parameter Optimization Engine

Three-stage optimization procedure for EEPAS model parameters:
- Stage 1: Optimize magnitude scaling (am, bm, Sm)
- Stage 2: Optimize temporal scaling (at, bt, St)
- Stage 3: Optimize spatial scaling (ba, Sa) and μ

Supports single-stage joint optimization and multiple optimizers.
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eepas_likelihood import eepas_likelihood
from utils.data_loader import DataLoader
from utils.fminsearchcon import fminsearchcon
from scipy.optimize import basinhopping, minimize, differential_evolution


def optimize_eepas_parameters(mj, xj, tj, yj, xi, yi, mi, ti,
                              me, xe, te, ye, W, EW, B, T1, T2, m0,
                              CELLE, params, config_file='config.json',
                              multi_start=False, n_starts=3, single_stage=False,
                              use_basinhopping=False, basinhopping_niter=20, optimizer='fminsearchcon',
                              region_manager=None, use_fast_mode=False, magnitude_samples=20,
                              lead_time_days=None):
    """
    Main function for EEPAS model parameter optimization.

    Seismological meaning:
        Estimates 8 EEPAS parameters to best fit foreshock-mainshock relationships in the earthquake catalog.

    Args:
        mj, xj, tj, yj: Target earthquakes (M≥mT, in testing region R during learning period) - paper's j
        xi, yi, mi, ti: Historical source earthquakes for PPE background (M≥mT, from neighborhood region N) - paper's i
        me, xe, te, ye: EEPAS foreshocks (M≥m₀)
        W: Aftershock de-weighting array (wᵢ, reduces aftershock foreshock status)
        EW: Weight average (E[W])
        B: Gutenberg-Richter b-value
        T1, T2: Learning time window
        m0: Completeness magnitude
        CELLE: Spatial grid definition
        params: Other model parameters (PPE parameters, delay, etc.)
        config_file: Configuration file path
        multi_start: Whether to use multi-start search (default False, enhances robustness but slower)
        n_starts: Number of starting points (default 3)
        single_stage: Whether to use single-stage full parameter optimization (default False, uses three-stage)
        use_fast_mode: Whether to use fast mode (default False)
            - True: Use Numba JIT accelerated midpoint rectangle method (fast)
            - False: Use accurate quad_vec integration (slow but precise)
        magnitude_samples: Number of sampling points in fast mode (default 20, increase for higher accuracy)
        lead_time_days: Fixed lead time L in days for FLEEPAS (default None)
            - None: Use all historical earthquakes as precursors (original EEPAS)
            - float: Only use earthquakes within [t-L, t-delay] as precursors (FLEEPAS)

    Returns:
        result: Dictionary containing optimal EEPAS parameters and negative log-likelihood
            {'am', 'bm', 'Sm', 'at', 'bt', 'St', 'ba', 'Sa', 'u', 'ln_likelihood'}
    """

    # Load configuration
    cfg = DataLoader.load_config(config_file)

    # ===== Output optimization task information =====
    if single_stage:
        print('\n╔══════════════════════════════════════════════════════════╗')
        print('║      EEPAS Single-Stage Full Parameter Optimization      ║')
        print('╠══════════════════════════════════════════════════════════╣')
        print(f'║ Target earthquakes (paper\'s j): {len(mj):<25d} ║')
        print(f'║ EEPAS earthquakes (M≥m₀): {len(me):<29d} ║')
        print(f'║ PPE source earthquakes (paper\'s i, M≥mT): {len(mi):<14d} ║')
        print('║                                                          ║')
        print('║ 🚀 Single-stage: Joint optimization of all 8 parameters ║')
        print('║    Optimizing: am, Sm, at, bt, St, ba, Sa, u            ║')
        print('║    Fixed: bm = 0.86                                     ║')
        print('╚══════════════════════════════════════════════════════════╝\n')
    else:
        print('\n╔══════════════════════════════════════════════════════════╗')
        print('║      EEPAS Three-Stage Parameter Optimization            ║')
        print('╠══════════════════════════════════════════════════════════╣')
        print(f'║ Target earthquakes (paper\'s j): {len(mj):<25d} ║')
        print(f'║ EEPAS earthquakes (M≥m₀): {len(me):<29d} ║')
        print(f'║ PPE source earthquakes (paper\'s i, M≥mT): {len(mi):<14d} ║')
        print('║                                                          ║')
        print('║ 📈 Stage 1: Optimize am, at, Sa, u                      ║')
        print('║    Fixed: bm=1, bt=0.3, Sm=0.2, St=0.15, ba=0.3         ║')
        print('║ 📈 Stage 2: Optimize Sm, bt, St, ba, u                  ║')
        print('║    Fixed: Stage 1 results for am, at, bm, Sa            ║')
        print('║ 📈 Stage 3: Joint optimization of all 8 parameters      ║')
        print('╚══════════════════════════════════════════════════════════╝\n')

    # ===== Pre-compute and cache PPE normalization integral =====
    # Seismological meaning: PPE background integral is invariant during optimization, pre-computation saves significant time
    # For 8-parameter optimization (potentially hundreds of objective function evaluations), caching can save hours of computation
    print('⚡ Pre-computing and caching PPE normalization integral...')
    if '_ppe_integral_cached' not in params:
        a = params['a']
        d = params['d']
        s = params['s']
        delay = params['delay']
        m0 = params['m0']
        mT = params['mT']
        mu = params.get('mu', 7.5)

        from ppe_optimization import calculate_ppe_normalization
        Xpol = np.column_stack([CELLE[:, 0], CELLE[:, 0], CELLE[:, 1], CELLE[:, 1]])
        Ypol = np.column_stack([CELLE[:, 2], CELLE[:, 3], CELLE[:, 3], CELLE[:, 2]])
        profile_opts = {'mu': mu, 'kernelMagFilter': 'mT', 'integralLower': 'mT'}

        integral_PPE, _, _, _ = calculate_ppe_normalization(
            a, d, s, B, xi, yi, mi, ti, Xpol, Ypol, CELLE, delay, m0, mT,
            profile_opts, tj, T1, T2, spatial_samples=40
        )

        params['_ppe_integral_cached'] = integral_PPE
        print(f'   ✓ PPE integral cached: {integral_PPE:.6f}')
    else:
        print(f'   ✓ Using cached PPE integral: {params["_ppe_integral_cached"]:.6f}')
    print()

    # ===== Single-stage full parameter optimization =====
    if single_stage:
        print('🚀 Single-stage optimization: Joint optimization of all 8 parameters')

        # Detect whether stage1 is configured for single-stage or three-stage
        # Single-stage: stage1 contains all 8 parameters
        # Three-stage: stage1 contains only partial parameters (need to read from stage1+stage2)
        stage1_config_type = DataLoader.detect_stage1_config_type(config_file)

        if stage1_config_type == 'single':
            # New format: stage1 contains complete single-stage configuration
            print('   📝 Reading single-stage configuration from stage1')

            stage1 = cfg['optimization']['stage1']

            # Read bm (fixed value)
            if 'fixedValues' not in stage1 or 'bm' not in stage1['fixedValues']:
                raise ValueError('stage1 must specify bm in fixedValues for single-stage optimization')
            bm = stage1['fixedValues']['bm']
            print(f'   Fixed parameter: bm = {bm:.2f}')

            # Read initial values, bounds from stage1
            # stage1 parameters should be: [am, Sm, at, bt, St, ba, Sa, u]
            parameters = stage1['parameters']
            initial_values = stage1['initialValues']
            lower_bounds = stage1['lowerBounds']
            upper_bounds = stage1['upperBounds']

            # Build x0_single, lb_single, ub_single in canonical order: [am, Sm, at, bt, St, ba, Sa, u]
            param_order = ['am', 'Sm', 'at', 'bt', 'St', 'ba', 'Sa', 'u']
            x0_single = np.zeros(8)
            lb_single = np.zeros(8)
            ub_single = np.zeros(8)

            for i, param in enumerate(param_order):
                if param not in parameters:
                    raise ValueError(f'Single-stage configuration missing parameter: {param}')
                idx = parameters.index(param)
                x0_single[i] = initial_values[idx]
                lb_single[i] = lower_bounds[idx]
                ub_single[i] = upper_bounds[idx]

        else:
            # Old format: read from stage1 + stage2 + stage3 (backward compatibility)
            print('   📝 Reading single-stage configuration from stage1+stage2+stage3 (legacy format)')

            # Read bm (fixed value) from configuration file
            bm = cfg['optimization']['stage3']['fixedValues']['bm']
            print(f'   Fixed parameter: bm = {bm:.2f}')

            # Initial values: Combine stage1 and stage2 initial values
            # stage1: [am, at, Sa, u]
            # stage2: [Sm, bt, St, ba, u]
            # stage3 order: [am, Sm, at, bt, St, ba, Sa, u]
            stage1_init = cfg['optimization']['stage1']['initialValues']  # [am, at, Sa, u]
            stage2_init = cfg['optimization']['stage2']['initialValues']  # [Sm, bt, St, ba, u]

            x0_single = np.array([
                stage1_init[0],  # am
                stage2_init[0],  # Sm
                stage1_init[1],  # at
                stage2_init[1],  # bt
                stage2_init[2],  # St
                stage2_init[3],  # ba
                stage1_init[2],  # Sa
                stage1_init[3]   # u
            ])

            # Boundary settings: Use stage3 bounds
            lb_single = np.array(cfg['optimization']['stage3']['lowerBounds'])
            ub_single = np.array(cfg['optimization']['stage3']['upperBounds'])

        print(f'   Initial values:')
        print(f'     am={x0_single[0]:.2f}, Sm={x0_single[1]:.2f}, at={x0_single[2]:.2f}, bt={x0_single[3]:.2f}')
        print(f'     St={x0_single[4]:.2f}, ba={x0_single[5]:.2f}, Sa={x0_single[6]:.2f}, u={x0_single[7]:.2f}')

        iteration_count = [0]
        def objective_single(P):
            """
            Single-stage objective function
            P = [am, Sm, at, bt, St, ba, Sa, u]
            """
            fd, _, _, _ = eepas_likelihood(
                P[0], bm, P[1], P[2], P[3], P[4], P[5], P[6], P[7],
                mj, xj, tj, yj, xi, yi, mi, ti, me, xe, te, ye,
                W, EW, B, T1, T2, m0, CELLE, params,
                region_manager=region_manager, use_fast_mode=use_fast_mode, magnitude_samples=magnitude_samples,
                lead_time_days=lead_time_days
            )
            iteration_count[0] += 1
            if iteration_count[0] % 10 == 0:
                print(f'   Iteration {iteration_count[0]:4d}: NLL = {fd:.6f}', flush=True)
            return fd

        # === Select optimization strategy ===
        if use_basinhopping:
            # Select local optimizer
            local_optimizer = optimizer if optimizer in ['L-BFGS-B', 'TNC', 'SLSQP'] else 'L-BFGS-B'
            print(f'   🏔️  Using Basin-Hopping global optimization (iterations={basinhopping_niter}, local optimizer={local_optimizer})...')

            # Basin-hopping requires boundary constraints
            from scipy.optimize import Bounds
            bounds = Bounds(lb_single, ub_single)

            # Silent objective function (basin-hopping calls it many times)
            def objective_silent(P):
                fd, _, _, _ = eepas_likelihood(
                    P[0], bm, P[1], P[2], P[3], P[4], P[5], P[6], P[7],
                    mj, xj, tj, yj, xi, yi, mi, ti, me, xe, te, ye,
                    W, EW, B, T1, T2, m0, CELLE, params,
                    region_manager=region_manager, use_fast_mode=use_fast_mode, magnitude_samples=magnitude_samples,
                    lead_time_days=lead_time_days
                )
                return fd

            # Basin-hopping callback to display progress
            bh_step = [0]
            bh_best = [np.inf]
            def bh_callback(x, f, accept):
                bh_step[0] += 1
                if f < bh_best[0]:
                    bh_best[0] = f
                    print(f'   → Step {bh_step[0]:3d}: NLL={f:.6f} {"✓Accepted" if accept else ""}', flush=True)
                return False

            result_bh = basinhopping(
                objective_silent,
                x0_single,
                niter=basinhopping_niter,
                minimizer_kwargs={
                    'method': local_optimizer,
                    'bounds': bounds,
                    'options': {'maxiter': 500, 'ftol': 1e-6}
                },
                callback=bh_callback,
                seed=42
            )

            x_final = result_bh.x
            fval_final = result_bh.fun
            exitflag = 0 if result_bh.lowest_optimization_result.success else 1
            output = {
                'iterations': bh_step[0],
                'funcCount': result_bh.nfev,
                'message': f'Basin-hopping completed with {bh_step[0]} steps'
            }
            print(f'   ✅ Basin-hopping completed: {bh_step[0]} steps, best NLL={fval_final:.6f}', flush=True)

        elif multi_start:
            print(f'   🎯 Using multi-start search ({n_starts} starting points, optimizer={optimizer})...')

            # Generate multiple starting points
            start_points = [x0_single]
            np.random.seed(42)
            for i in range(n_starts - 1):
                # Perturb around initial value (±30% range)
                perturbation = 0.3 * (2 * np.random.rand(len(x0_single)) - 1)
                random_start = x0_single * (1 + perturbation)
                random_start = np.clip(random_start, lb_single, ub_single)
                start_points.append(random_start)

            # Store all candidate solutions
            candidates = []

            for i, start_point in enumerate(start_points):
                print(f'\n   Starting point {i+1}/{n_starts}:')
                print(f'     am={start_point[0]:.2f}, Sm={start_point[1]:.2f}, at={start_point[2]:.2f}, bt={start_point[3]:.2f}')
                print(f'     St={start_point[4]:.2f}, ba={start_point[5]:.2f}, Sa={start_point[6]:.2f}, u={start_point[7]:.2f}')

                iteration_count[0] = 0  # Reset counter

                if optimizer == 'fminsearchcon':
                    x_temp, fval_temp, exitflag_temp, output_temp = fminsearchcon(
                        objective_single, start_point,
                        lb=lb_single, ub=ub_single,
                        options={'maxiter': 10000, 'maxfun': 10000, 'xtol': 1e-8, 'ftol': 1e-6, 'disp': False}
                    )
                elif optimizer in ['L-BFGS-B', 'TNC', 'SLSQP', 'Powell']:
                    if optimizer == 'L-BFGS-B':
                        # L-BFGS-B: Tighten tolerances (1e-6 still too loose → 1e-7)
                        result = minimize(
                            objective_single, start_point,
                            method=optimizer,
                            bounds=list(zip(lb_single, ub_single)),
                            options={'maxiter': 10000, 'maxfun': 10000, 'ftol': 1e-9, 'gtol': 1e-7, 'disp': False}
                        )
                    elif optimizer == 'TNC':
                        # TNC: Keep original settings (performs reasonably)
                        result = minimize(
                            objective_single, start_point,
                            method=optimizer,
                            bounds=list(zip(lb_single, ub_single)),
                            options={'maxiter': 10000, 'maxfun': 10000, 'ftol': 1e-9, 'gtol': 1e-3, 'xtol': 1e-8, 'disp': False}
                        )
                    elif optimizer == 'SLSQP':
                        # SLSQP: Tighten tolerances (1e-10 still too loose → 1e-12)
                        result = minimize(
                            objective_single, start_point,
                            method=optimizer,
                            bounds=list(zip(lb_single, ub_single)),
                            options={'maxiter': 10000, 'ftol': 1e-12, 'disp': False}
                        )
                    elif optimizer == 'Powell':
                        # Powell uses absolute ftol (same as fmin)
                        result = minimize(
                            objective_single, start_point,
                            method=optimizer,
                            bounds=list(zip(lb_single, ub_single)),
                            options={'maxiter': 10000, 'maxfev': 10000, 'ftol': 1e-6, 'xtol': 1e-8, 'disp': False}
                        )
                    x_temp = result.x
                    fval_temp = result.fun
                    exitflag_temp = 0 if result.success else 1
                    output_temp = {
                        'iterations': result.nit if hasattr(result, 'nit') else 0,
                        'funcCount': result.nfev,
                        'message': result.message
                    }
                else:
                    raise ValueError(f'Unsupported optimizer: {optimizer}')

                print(f'   → Completed: NLL={fval_temp:.6f}', flush=True)
                candidates.append((x_temp, fval_temp, exitflag_temp, output_temp))

            # Select the best
            best_idx = np.argmin([c[1] for c in candidates])
            x_final, fval_final, exitflag, output = candidates[best_idx]

            print(f'\n   ✅ Best starting point: {best_idx+1}/{n_starts}, NLL={fval_final:.6f}', flush=True)

        else:
            print(f'   Starting optimization (using {optimizer})...')
            # Standard single starting point optimization
            if optimizer == 'fminsearchcon':
                x_final, fval_final, exitflag, output = fminsearchcon(
                    objective_single, x0_single,
                    lb=lb_single, ub=ub_single,
                    options={'maxiter': 10000, 'maxfun': 10000, 'xtol': 1e-8, 'ftol': 1e-6, 'disp': False}
                )
            elif optimizer in ['L-BFGS-B', 'TNC', 'SLSQP', 'Powell']:
                if optimizer == 'L-BFGS-B':
                    # L-BFGS-B: Tighten tolerances (1e-6 still too loose → 1e-7)
                    result = minimize(
                        objective_single, x0_single,
                        method=optimizer,
                        bounds=list(zip(lb_single, ub_single)),
                        options={'maxiter': 10000, 'maxfun': 10000, 'ftol': 1e-9, 'gtol': 1e-7}
                    )
                elif optimizer == 'TNC':
                    # TNC: Keep original settings (performs reasonably)
                    result = minimize(
                        objective_single, x0_single,
                        method=optimizer,
                        bounds=list(zip(lb_single, ub_single)),
                        options={'maxiter': 10000, 'maxfun': 10000, 'ftol': 1e-9, 'gtol': 1e-3, 'xtol': 1e-8}
                    )
                elif optimizer == 'SLSQP':
                    # SLSQP: Tighten tolerances (1e-10 still too loose → 1e-12)
                    result = minimize(
                        objective_single, x0_single,
                        method=optimizer,
                        bounds=list(zip(lb_single, ub_single)),
                        options={'maxiter': 10000, 'ftol': 1e-12}
                    )
                elif optimizer == 'Powell':
                    # Powell uses absolute ftol (same as fmin)
                    result = minimize(
                        objective_single, x0_single,
                        method=optimizer,
                        bounds=list(zip(lb_single, ub_single)),
                        options={'maxiter': 10000, 'maxfev': 10000, 'ftol': 1e-6, 'xtol': 1e-8}
                    )
                x_final = result.x
                fval_final = result.fun
                exitflag = 0 if result.success else 1
                output = {
                    'iterations': result.nit if hasattr(result, 'nit') else 0,
                    'funcCount': result.nfev,
                    'message': result.message
                }
            else:
                raise ValueError(f'Unsupported optimizer: {optimizer}')

        print(f'\n   ✅ Single-stage optimization completed', flush=True)
        print(f'   exitflag: {exitflag}', flush=True)
        print(f'   Iterations: {output.get("iterations", "N/A")}', flush=True)
        print(f'   Function evaluations: {output.get("funcCount", "N/A")}', flush=True)
        print(f'   Termination reason: {output.get("message", "N/A")}', flush=True)
        print(f'   Final parameters:', flush=True)
        print(f'     am={x_final[0]:.6f}, bm={bm:.6f}, Sm={x_final[1]:.6f}', flush=True)
        print(f'     at={x_final[2]:.6f}, bt={x_final[3]:.6f}, St={x_final[4]:.6f}', flush=True)
        print(f'     ba={x_final[5]:.6f}, Sa={x_final[6]:.6f}, u={x_final[7]:.6f}', flush=True)
        print(f'   Final NLL: {fval_final:.6f}\n', flush=True)

        # Return results
        result = {
            'am': x_final[0],
            'bm': bm,
            'Sm': x_final[1],
            'at': x_final[2],
            'bt': x_final[3],
            'St': x_final[4],
            'ba': x_final[5],
            'Sa': x_final[6],
            'u': x_final[7],
            'ln_likelihood': -fval_final
        }

        return result

    # ===== Stage 1: Optimize am, at, Sa, u =====
    # Seismological meaning:
    #   - Fix slope parameters (bm, bt, ba), first determine intercepts and spatial scale
    #   - am: Magnitude intercept (baseline for foreshock-mainshock magnitude prediction)
    #   - at: Time intercept (baseline for foreshock-mainshock time prediction)
    #   - Sa: Spatial standard deviation (baseline for foreshock-mainshock location prediction)
    #   - u: failure-to-predict rate (proportion of earthquakes without foreshock signals)
    print('🔄 Stage 1: Optimize am, at, Sa, u')

    # Read fixed parameter values from configuration file
    fixedVals = cfg['optimization']['stage1']['fixedValues']
    bm = fixedVals['bm']  # Magnitude slope (fixed at 1, linear relationship)
    Sm = fixedVals['Sm']  # Magnitude standard deviation (initial assumption)
    bt = fixedVals['bt']  # Time slope (fixed at 0.3, typical empirical value)
    St = fixedVals['St']  # Time standard deviation (initial assumption)
    ba = fixedVals['ba']  # Spatial slope (fixed at 0.3, magnitude increase of 1 doubles spatial range)

    print(f'   Fixed parameters: bm={bm:.2f}, Sm={Sm:.2f}, bt={bt:.2f}, St={St:.2f}, ba={ba:.2f}')

    # Read optimization initial values and bounds
    x0_stage1 = np.array(cfg['optimization']['stage1']['initialValues'])
    lb_stage1 = np.array(cfg['optimization']['stage1']['lowerBounds'])
    ub_stage1 = np.array(cfg['optimization']['stage1']['upperBounds'])

    print(f'   Initial values: am={x0_stage1[0]:.2f}, at={x0_stage1[1]:.2f}, Sa={x0_stage1[2]:.2f}, u={x0_stage1[3]:.2f}')
    print('   Starting optimization...')

    # Define objective function (Stage 1)
    iteration_count = [0]  # Iteration counter (use list to allow modification in nested function)
    def objective_stage1(P):
        """
        Stage 1 objective function
        P = [am, at, Sa, u]
        """
        # Call EEPAS likelihood function to compute NLL
        fd, _, _, _ = eepas_likelihood(
            P[0], bm, Sm, P[1], bt, St, ba, P[2], P[3],  # 8 parameters (4 optimized + 5 fixed)
            mj, xj, tj, yj, xi, yi, mi, ti, me, xe, te, ye,
            W, EW, B, T1, T2, m0, CELLE, params,
            region_manager=region_manager, use_fast_mode=use_fast_mode, magnitude_samples=magnitude_samples,
            lead_time_days=lead_time_days
        )
        # Output progress every 10 iterations
        iteration_count[0] += 1
        if iteration_count[0] == 1 or iteration_count[0] % 10 == 0:
            print(f'   Iteration {iteration_count[0]:4d}: NLL = {fd:.6f}, am={P[0]:.4f}, at={P[1]:.4f}, Sa={P[2]:.4f}, u={P[3]:.6f}', flush=True)
        return fd

    # Use constrained optimizer (Nelder-Mead with bounds)
    # Tolerance settings consistent with MATLAB: xtol=1e-8, ftol=1e-8
    x_stage1, fval_stage1, exitflag, output = fminsearchcon(
        objective_stage1, x0_stage1,
        lb=lb_stage1, ub=ub_stage1,
        options={'maxiter': 5000, 'xtol': 1e-8, 'ftol': 1e-8, 'disp': False}
    )

    result_stage1 = type('obj', (object,), {'x': x_stage1, 'fun': fval_stage1})()

    x_stage1 = result_stage1.x
    print(f'\n   ✅ Stage 1 completed', flush=True)
    print(f'   Best values: am={x_stage1[0]:.6f}, at={x_stage1[1]:.6f}, Sa={x_stage1[2]:.6f}, u={x_stage1[3]:.6f}', flush=True)
    print(f'   Stage NLL: {result_stage1.fun:.6f}\n', flush=True)

    am, at, Sa, u = x_stage1

    # ===== Stage 2: Optimize Sm, bt, St, ba, u =====
    # Seismological meaning:
    #   - Fix Stage 1 results (am, at, bm, Sa), fine-tune variance and slope parameters
    #   - Sm: Magnitude standard deviation (dispersion in foreshock-mainshock magnitude prediction)
    #   - bt: Time slope (influence of magnitude on precursor time)
    #   - St: Time standard deviation (dispersion in precursor time)
    #   - ba: Spatial slope (influence of magnitude on foreshock spatial extent)
    #   - u: Re-optimize failure-to-predict rate
    print('🔄 Stage 2: Optimize Sm, bt, St, ba, u', flush=True)

    # Initial values (u uses Stage 1 result)
    init_vals_stage2 = cfg['optimization']['stage2']['initialValues']
    x0_stage2 = []
    for val in init_vals_stage2:
        if isinstance(val, str) and 'u_from_stage1' in val:
            x0_stage2.append(u)
        else:
            x0_stage2.append(float(val))
    x0_stage2 = np.array(x0_stage2)

    lb_stage2 = np.array(cfg['optimization']['stage2']['lowerBounds'])
    ub_stage2 = np.array(cfg['optimization']['stage2']['upperBounds'])

    def objective_stage2(P):
        fd, _, _, _ = eepas_likelihood(
            am, bm, P[0], at, P[1], P[2], P[3], Sa, P[4],
            mj, xj, tj, yj, xi, yi, mi, ti, me, xe, te, ye,
            W, EW, B, T1, T2, m0, CELLE, params,
            region_manager=region_manager, use_fast_mode=use_fast_mode, magnitude_samples=magnitude_samples,
            lead_time_days=lead_time_days
        )
        return fd

    # Use Differential Evolution global optimization (insensitive to initial values and fast)
    use_differential_evolution = False

    if use_differential_evolution:
        print(f'   🧬 Using Differential Evolution global optimization', flush=True)

        # Boundary constraints (convert to list of (min, max) tuples)
        bounds_list = list(zip(lb_stage2, ub_stage2))

        # Callback to display progress
        de_iter = [0]
        de_best = [np.inf]
        def de_callback(xk, convergence):
            de_iter[0] += 1
            fval = objective_stage2(xk)
            if fval < de_best[0]:
                de_best[0] = fval
                print(f'   → Iteration {de_iter[0]}: NLL={fval:.6f}, Sm={xk[0]:.3f}', flush=True)
            return False

        result_de = differential_evolution(
            objective_stage2,
            bounds_list,
            strategy='best1bin',
            maxiter=30,   # Reduce iterations for speed
            popsize=10,   # Reduce population size
            tol=1e-6,     # Relax tolerance
            seed=42,
            disp=False,
            workers=1,
            callback=de_callback
        )

        x_stage2 = result_de.x
        fval_stage2 = result_de.fun
        print(f'   ✅ Differential Evolution completed: {de_iter[0]} generations, best NLL={fval_stage2:.6f}', flush=True)
        result_stage2 = type('obj', (object,), {'x': x_stage2, 'fun': fval_stage2})()

    elif multi_start:
        print(f'   🎯 Using multi-start search ({n_starts} starting points) + Stage 3 quick evaluation', flush=True)

        # Prepare Stage 3 bounds in advance
        lb_stage3 = np.array(cfg['optimization']['stage3']['lowerBounds'])
        ub_stage3 = np.array(cfg['optimization']['stage3']['upperBounds'])

        # Generate multiple starting points - perturb around initial values rather than completely random
        start_points = [x0_stage2]
        np.random.seed(42)  # Fix random seed to ensure reproducibility
        for i in range(n_starts - 1):
            # Perturb around initial values (±50% range)
            perturbation = 0.5 * (2 * np.random.rand(len(x0_stage2)) - 1)  # [-0.5, 0.5]
            random_start = x0_stage2 * (1 + perturbation)
            random_start[4] = u + np.random.randn() * 0.05  # u perturbed around stage 1 result
            random_start = np.clip(random_start, lb_stage2, ub_stage2)
            start_points.append(random_start)

        # Store all candidate solutions
        candidates = []

        for i, start_point in enumerate(start_points):
            print(f'   Starting point {i+1}/{n_starts}: Sm={start_point[0]:.2f}, bt={start_point[1]:.2f}, St={start_point[2]:.2f}, ba={start_point[3]:.2f}, u={start_point[4]:.2f}', flush=True)

            x_temp, fval_temp, _, _ = fminsearchcon(
                objective_stage2, start_point,
                lb=lb_stage2, ub=ub_stage2,
                options={'maxiter': 5000, 'xtol': 1e-8, 'ftol': 1e-8, 'disp': False}
            )

            print(f'   → Stage 2 NLL={fval_temp:.6f}, Sm={x_temp[0]:.3f}', flush=True)

            # Quick evaluation of Stage 3 final effect
            x0_stage3_test = np.array([am, x_temp[0], at, x_temp[1], x_temp[2], x_temp[3], Sa, x_temp[4]])

            def objective_stage3_test(P):
                fd, _, _, _ = eepas_likelihood(
                    P[0], bm, P[1], P[2], P[3], P[4], P[5], P[6], P[7],
                    mj, xj, tj, yj, xi, yi, mi, ti, me, xe, te, ye,
                    W, EW, B, T1, T2, m0, CELLE, params,
                    region_manager=region_manager, use_fast_mode=use_fast_mode, magnitude_samples=magnitude_samples,
                    lead_time_days=lead_time_days
                )
                return fd

            # Quick 500-step optimization for evaluation (need enough steps to see difference)
            x_test, fval_test, _, _ = fminsearchcon(
                objective_stage3_test, x0_stage3_test,
                lb=lb_stage3, ub=ub_stage3,
                options={'maxiter': 500, 'xtol': 1e-6, 'ftol': 1e-6, 'disp': False}
            )

            print(f'   → Stage 3 quick evaluation NLL={fval_test:.6f}', flush=True)
            candidates.append((x_temp, fval_temp, fval_test))

        # Select best based on Stage 3 evaluation
        best_idx = np.argmin([c[2] for c in candidates])
        x_stage2 = candidates[best_idx][0]
        fval_stage2 = candidates[best_idx][1]
        print(f'   ✨ Selected starting point {best_idx+1}: Stage 2 NLL={fval_stage2:.6f}, Stage 3 evaluation NLL={candidates[best_idx][2]:.6f}', flush=True)

        result_stage2 = type('obj', (object,), {'x': x_stage2, 'fun': fval_stage2})()
    else:
        print(f'   Initial values: Sm={x0_stage2[0]:.2f}, bt={x0_stage2[1]:.2f}, St={x0_stage2[2]:.2f}, ba={x0_stage2[3]:.2f}, u={x0_stage2[4]:.2f}', flush=True)
        print('   Starting optimization...', flush=True)

        iteration_count[0] = 0
        def objective_stage2_verbose(P):
            fd = objective_stage2(P)
            iteration_count[0] += 1
            if iteration_count[0] % 10 == 0:
                print(f'   Iteration {iteration_count[0]:4d}: NLL = {fd:.6f}', flush=True)
            return fd

        x_stage2, fval_stage2, exitflag, output = fminsearchcon(
            objective_stage2_verbose, x0_stage2,
            lb=lb_stage2, ub=ub_stage2,
            options={'maxiter': 5000, 'xtol': 1e-8, 'ftol': 1e-8, 'disp': False}
        )
        result_stage2 = type('obj', (object,), {'x': x_stage2, 'fun': fval_stage2})()

    x_stage2 = result_stage2.x
    print(f'   ✅ Stage 2 completed', flush=True)
    print(f'   Best values: Sm={x_stage2[0]:.6f}, bt={x_stage2[1]:.6f}, St={x_stage2[2]:.6f}, ba={x_stage2[3]:.6f}, u={x_stage2[4]:.6f}', flush=True)
    print(f'   Stage objective value: {result_stage2.fun:.6f}\n', flush=True)

    Sm, bt, St, ba, u = x_stage2

    # ===== Stage 3: Joint optimization of all 8 parameters =====
    # Seismological meaning:
    #   - Based on Stages 1 and 2 results, globally optimize all parameters for best fit
    #   - Simultaneously adjust all parameters to capture parameter interactions
    #   - P = [am, Sm, at, bt, St, ba, Sa, u] (bm fixed at 1)
    print('🔄 Stage 3: Joint optimization of all parameters', flush=True)

    # Use Stages 1 and 2 results as initial values
    x0_stage3 = np.array([am, Sm, at, bt, St, ba, Sa, u])
    lb_stage3 = np.array(cfg['optimization']['stage3']['lowerBounds'])
    ub_stage3 = np.array(cfg['optimization']['stage3']['upperBounds'])

    print(f'   Initial values: [{", ".join([f"{v:.2f}" for v in x0_stage3])}]', flush=True)
    print('   Starting optimization...', flush=True)

    iteration_count[0] = 0
    def objective_stage3(P):
        """
        Stage 3 objective function
        P = [am, Sm, at, bt, St, ba, Sa, u]
        """
        fd, _, _, _ = eepas_likelihood(
            P[0], bm, P[1], P[2], P[3], P[4], P[5], P[6], P[7],  # 8 parameters (bm=1 fixed)
            mj, xj, tj, yj, xi, yi, mi, ti, me, xe, te, ye,
            W, EW, B, T1, T2, m0, CELLE, params,
            region_manager=region_manager, use_fast_mode=use_fast_mode, magnitude_samples=magnitude_samples,
            lead_time_days=lead_time_days
        )
        iteration_count[0] += 1
        if iteration_count[0] % 10 == 0:
            print(f'   Iteration {iteration_count[0]:4d}: NLL = {fd:.6f}', flush=True)
        return fd

    # Use fminsearchcon
    # Enhanced convergence: Increase maxiter and maxfun and reduce tolerance to match MATLAB
    # Bug fix: Must set both maxiter and maxfun, otherwise limited by maxfun default (200*n)
    # ftol set to 1e-6: Too small causes premature stop at local oscillations, too large causes insufficient convergence
    # Testing shows ~3000 function evaluations needed for adequate convergence
    x_final, fval_final, exitflag, output = fminsearchcon(
        objective_stage3, x0_stage3,
        lb=lb_stage3, ub=ub_stage3,
        options={'maxiter': 10000, 'maxfun': 10000, 'xtol': 1e-8, 'ftol': 1e-6, 'disp': False}
    )

    result_stage3 = type('obj', (object,), {'x': x_final, 'fun': fval_final})()

    x_final = result_stage3.x
    print(f'   ✅ Stage 3 completed', flush=True)
    print(f'   exitflag: {exitflag}', flush=True)
    print(f'   Iterations: {output.get("iterations", "N/A")}', flush=True)
    print(f'   Function evaluations: {output.get("funcCount", "N/A")}', flush=True)
    print(f'   Termination reason: {output.get("message", "N/A")}', flush=True)
    print(f'   Final parameters:', flush=True)
    print(f'     am={x_final[0]:.6f}, bm={bm:.6f}, Sm={x_final[1]:.6f}', flush=True)
    print(f'     at={x_final[2]:.6f}, bt={x_final[3]:.6f}, St={x_final[4]:.6f}', flush=True)
    print(f'     ba={x_final[5]:.6f}, Sa={x_final[6]:.6f}, u={x_final[7]:.6f}', flush=True)
    print(f'   Final objective value: {result_stage3.fun:.6f}\n', flush=True)

    # Return results
    result = {
        'am': x_final[0],
        'bm': bm,
        'Sm': x_final[1],
        'at': x_final[2],
        'bt': x_final[3],
        'St': x_final[4],
        'ba': x_final[5],
        'Sa': x_final[6],
        'u': x_final[7],
        'ln_likelihood': -result_stage3.fun
    }

    return result


def optimize_custom_stages(mj, xj, tj, yj, xi, yi, mi, ti,
                           me, xe, te, ye, W, EW, B, T1, T2, m0,
                           CELLE, params, config_file='config.json',
                           optimizer='SLSQP',
                           region_manager=None, use_fast_mode=False, magnitude_samples=20,
                           lead_time_days=None):
    """
    Custom stages EEPAS parameter optimization.

    Allows users to define arbitrary number of stages and which parameters to optimize in each stage.
    All parameters are automatically inherited from previous stages.

    Args:
        mj, xj, tj, yj: Target earthquakes
        xi, yi, mi, ti: PPE source earthquakes
        me, xe, te, ye: EEPAS foreshocks
        W, EW, B, T1, T2, m0: Model parameters
        CELLE: Spatial grid
        params: Other model parameters
        config_file: Configuration file path (must have customStages enabled)
        optimizer: Optimizer to use ('SLSQP', 'L-BFGS-B', 'fminsearchcon')
        region_manager: Region manager instance
        use_fast_mode: Whether to use fast mode
        magnitude_samples: Magnitude sampling points
        lead_time_days: Fixed lead time L in days for FLEEPAS (default None)

    Returns:
        dict: Final optimized parameters
    """
    # Load configuration
    cfg = DataLoader.load_config(config_file)
    custom_config = DataLoader.load_custom_stages(config_file)

    if custom_config is None:
        raise ValueError('customStages not enabled in configuration file')

    stages = custom_config['stages']
    num_stages = len(stages)

    print('\n' + '='*80)
    print(f'EEPAS Custom Stages Optimization ({num_stages} stages)')
    print('='*80)
    print(f'Target earthquakes: {len(mj)}')
    print(f'EEPAS earthquakes (M≥m₀): {len(me)}')
    print(f'PPE source earthquakes (M≥mT): {len(mi)}')
    print(f'Optimizer: {optimizer}')
    print('='*80)
    print()

    # Pre-compute PPE normalization integral (same as standard optimization)
    print('⚡ Pre-computing and caching PPE normalization integral...')
    if '_ppe_integral_cached' not in params:
        a = params['a']
        d = params['d']
        s = params['s']
        delay = params['delay']
        m0_param = params['m0']
        mT = params['mT']
        mu = params.get('mu', 7.5)

        from ppe_optimization import calculate_ppe_normalization
        Xpol = np.column_stack([CELLE[:, 0], CELLE[:, 0], CELLE[:, 1], CELLE[:, 1]])
        Ypol = np.column_stack([CELLE[:, 2], CELLE[:, 3], CELLE[:, 3], CELLE[:, 2]])
        profile_opts = {'mu': mu, 'kernelMagFilter': 'mT', 'integralLower': 'mT'}

        integral_PPE, _, _, _ = calculate_ppe_normalization(
            a, d, s, B, xi, yi, mi, ti, Xpol, Ypol, CELLE, delay, m0_param, mT,
            profile_opts, tj, T1, T2, spatial_samples=40
        )

        params['_ppe_integral_cached'] = integral_PPE
        print(f'   ✓ PPE integral cached: {integral_PPE:.6f}')
    else:
        print(f'   ✓ Using cached PPE integral: {params["_ppe_integral_cached"]:.6f}')
    print()

    # Parameter order in EEPAS likelihood function
    param_order = ['am', 'bm', 'Sm', 'at', 'bt', 'St', 'ba', 'Sa', 'u']

    # Current parameter values (will be updated after each stage)
    current_params = {}

    # Execute each stage
    stage_results = []

    for stage_idx, stage in enumerate(stages):
        stage_num = stage_idx + 1
        stage_name = stage.get('name', f'Stage {stage_num}')

        print(f'\n{"="*80}')
        print(f'🔄 {stage_name} ({stage_num}/{num_stages})')
        print(f'{"="*80}')

        # Get stage configuration
        opt_params = stage['parameters']  # Parameters to optimize
        lower_bounds = np.array(stage['lowerBounds'])
        upper_bounds = np.array(stage['upperBounds'])
        initial_values = stage.get('initialValues', None)
        fixed_values = stage.get('fixedValues', {})

        # Build initial values for this stage
        x0_stage = []

        if initial_values is None:
            # Use inherited values from previous stage
            print(f'   Initial values: inherited from previous stage')
            for param in opt_params:
                if param in current_params:
                    x0_stage.append(current_params[param])
                else:
                    raise ValueError(f'{stage_name}: parameter "{param}" not initialized and no initialValues provided')
        else:
            # Use provided initial values
            print(f'   Initial values: provided in configuration')
            x0_stage = list(initial_values)

        x0_stage = np.array(x0_stage)

        # Build full parameter set for this stage
        # Combine: optimized parameters (from x0_stage) + fixed parameters + inherited parameters
        stage_param_dict = current_params.copy()  # Start with inherited
        stage_param_dict.update(fixed_values)     # Override with fixed values

        # Display optimization info
        print(f'   Optimizing {len(opt_params)} parameters: {", ".join(opt_params)}')
        if len(fixed_values) > 0:
            print(f'   Fixed {len(fixed_values)} parameters: {", ".join(fixed_values.keys())}')
        inherited = set(param_order) - set(opt_params) - set(fixed_values.keys())
        if len(inherited) > 0 and stage_idx > 0:
            print(f'   Inherited {len(inherited)} parameters from previous stage: {", ".join(inherited)}')

        # Display initial values
        init_str = ', '.join([f'{p}={v:.4f}' for p, v in zip(opt_params, x0_stage)])
        print(f'   Initial: {init_str}')
        print()

        # Define objective function for this stage
        iteration_count = [0]

        def objective_stage(P):
            """
            Objective function for current stage
            P contains only the parameters being optimized
            """
            # Update stage parameter dict with current optimization values
            temp_dict = stage_param_dict.copy()
            for i, param in enumerate(opt_params):
                temp_dict[param] = P[i]

            # Build parameter array in correct order
            param_array = [temp_dict[p] for p in param_order]

            # Call EEPAS likelihood
            fd, _, _, _ = eepas_likelihood(
                param_array[0], param_array[1], param_array[2],  # am, bm, Sm
                param_array[3], param_array[4], param_array[5],  # at, bt, St
                param_array[6], param_array[7], param_array[8],  # ba, Sa, u
                mj, xj, tj, yj, xi, yi, mi, ti, me, xe, te, ye,
                W, EW, B, T1, T2, m0, CELLE, params,
                region_manager=region_manager, use_fast_mode=use_fast_mode,
                magnitude_samples=magnitude_samples, lead_time_days=lead_time_days
            )

            iteration_count[0] += 1
            if iteration_count[0] % 10 == 0:
                param_str = ', '.join([f'{p}={P[i]:.4f}' for i, p in enumerate(opt_params)])
                print(f'   Iteration {iteration_count[0]:4d}: NLL={fd:.6f} ({param_str})', flush=True)

            return fd

        # Execute optimization
        print(f'   Starting optimization (optimizer={optimizer})...')

        if optimizer == 'fminsearchcon':
            x_final, fval_final, exitflag, output = fminsearchcon(
                objective_stage, x0_stage,
                lb=lower_bounds, ub=upper_bounds,
                options={'maxiter': 10000, 'maxfun': 10000, 'xtol': 1e-8, 'ftol': 1e-6, 'disp': False}
            )
        elif optimizer in ['L-BFGS-B', 'TNC', 'SLSQP', 'Powell']:
            if optimizer == 'L-BFGS-B':
                result = minimize(
                    objective_stage, x0_stage,
                    method=optimizer,
                    bounds=list(zip(lower_bounds, upper_bounds)),
                    options={'maxiter': 10000, 'ftol': 1e-9, 'gtol': 1e-7}
                )
            elif optimizer == 'TNC':
                result = minimize(
                    objective_stage, x0_stage,
                    method=optimizer,
                    bounds=list(zip(lower_bounds, upper_bounds)),
                    options={'maxiter': 10000, 'ftol': 1e-9, 'gtol': 1e-3, 'xtol': 1e-8}
                )
            elif optimizer == 'SLSQP':
                result = minimize(
                    objective_stage, x0_stage,
                    method=optimizer,
                    bounds=list(zip(lower_bounds, upper_bounds)),
                    options={'maxiter': 10000, 'ftol': 1e-12}
                )
            elif optimizer == 'Powell':
                result = minimize(
                    objective_stage, x0_stage,
                    method=optimizer,
                    bounds=list(zip(lower_bounds, upper_bounds)),
                    options={'maxiter': 10000, 'ftol': 1e-6, 'xtol': 1e-8}
                )

            x_final = result.x
            fval_final = result.fun
            exitflag = 0 if result.success else 1
            output = {
                'iterations': result.nit if hasattr(result, 'nit') else 0,
                'funcCount': result.nfev,
                'message': result.message
            }
        else:
            raise ValueError(f'Unsupported optimizer: {optimizer}')

        # Update current parameters with optimized values
        for i, param in enumerate(opt_params):
            current_params[param] = x_final[i]

        # Also update with fixed values (for next stage)
        current_params.update(fixed_values)

        # Store stage result
        stage_result = {
            'stage': stage_num,
            'name': stage_name,
            'nll': fval_final,
            'exitflag': exitflag,
            'iterations': output.get('iterations', 'N/A'),
            'funcCount': output.get('funcCount', 'N/A'),
            'parameters': {param: x_final[i] for i, param in enumerate(opt_params)}
        }
        stage_results.append(stage_result)

        # Display results
        print(f'\n   ✅ {stage_name} completed')
        print(f'   Exit flag: {exitflag}')
        print(f'   Iterations: {output.get("iterations", "N/A")}')
        print(f'   Function evaluations: {output.get("funcCount", "N/A")}')
        optimized_str = ', '.join([f'{p}={x_final[i]:.6f}' for i, p in enumerate(opt_params)])
        print(f'   Optimized: {optimized_str}')
        print(f'   Stage NLL: {fval_final:.6f}')

    # Display final summary
    print(f'\n{"="*80}')
    print(f'✅ All {num_stages} stages completed')
    print(f'{"="*80}')
    print(f'Final parameters:')
    for param in param_order:
        print(f'   {param} = {current_params[param]:.6f}')
    print(f'Final NLL: {stage_results[-1]["nll"]:.6f}')
    print('='*80)
    print()

    # Return final result in standard format
    result = {
        'am': current_params['am'],
        'bm': current_params['bm'],
        'Sm': current_params['Sm'],
        'at': current_params['at'],
        'bt': current_params['bt'],
        'St': current_params['St'],
        'ba': current_params['ba'],
        'Sa': current_params['Sa'],
        'u': current_params['u'],
        'ln_likelihood': -stage_results[-1]['nll']
    }

    return result