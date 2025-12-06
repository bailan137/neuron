import os

cad_code_clean = """
TITLE Decay of internal calcium concentration

NEURON {
    SUFFIX cad
    USEION ca READ ica, cai WRITE cai
    RANGE depth, tau, cai0
}

UNITS {
    (mM) = (milli/liter)
    (mA) = (milliamp)
    F = (faraday) (coulomb)
}

PARAMETER {
    depth = 0.1 (um)      : depth of shell
    tau = 50 (ms)         : decay time constant
    cai0 = 1e-4 (mM)      : initial concentration
}

ASSIGNED {
    ica (mA/cm2)
}

STATE {
    cai (mM)
}

INITIAL {
    cai = cai0
}

BREAKPOINT {
    SOLVE state METHOD cnexp
}

DERIVATIVE state {
    cai' = -(10000)*(ica)/(2*F*depth) - (cai - cai0)/tau
}
"""

with open('cad.mod', 'w') as f:
    f.write(cad_code_clean)
print("Created clean cad.mod")

ca_hva_code_clean = """
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
"""

with open('ca_hva.mod', 'w') as f:
    f.write(ca_hva_code_clean)
print("Created clean ca_hva.mod")