
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
