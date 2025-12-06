
TITLE High Voltage Activated Calcium channel

UNITS {
    (mV) = (millivolt)
    (mA) = (milliamp)
    (S) = (siemens)
}

NEURON {
    SUFFIX ca_hva
    USEION ca READ eca WRITE ica
    RANGE gbar, ica
}

PARAMETER {
    gbar = 0.0001 (S/cm2)
    eca = 120 (mV)
}

STATE { m h }

ASSIGNED {
    v (mV)
    ica (mA/cm2)
    minf hinf
    mtau (ms) htau (ms)
}

BREAKPOINT {
    SOLVE states METHOD cnexp
    ica = gbar * m * m * h * (v - eca)
}

INITIAL {
    rates(v)
    m = minf
    h = hinf
}

DERIVATIVE states {
    rates(v)
    m' = (minf - m) / mtau
    h' = (hinf - h) / htau
}

PROCEDURE rates(v (mV)) {
    LOCAL alpha, beta
    
    : m - activation
    alpha = 0.055 * (-27 - v) / (exp((-27 - v)/3.8) - 1)
    beta = 0.94 * exp((-75 - v)/17)
    mtau = 1 / (alpha + beta)
    minf = alpha * mtau

    : h - inactivation
    alpha = 0.000457 * exp((-13 - v)/50)
    beta = 0.0065 / (exp((-15 - v)/28) + 1)
    htau = 1 / (alpha + beta)
    hinf = alpha * htau
}
