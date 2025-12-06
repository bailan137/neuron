from neuron import h
import matplotlib.pyplot as plt
import numpy as np
import random

h.load_file('stdrun.hoc')
try:
    h.nrn_load_dll('./x86_64/.libs/libnrnmech.so') 
except:
    print("Warning")

def build_model():
    soma = h.Section(name='soma')
    dend = h.Section(name='dend')
    dend.connect(soma(1))

    soma.L = 20; soma.diam = 20
    dend.L = 500; dend.diam = 2; dend.nseg = 51 

    for sec in h.allsec():
        sec.Ra = 150   
        sec.cm = 1     

    soma.insert('hh')
    soma.gnabar_hh = 0.3
    soma.gkbar_hh = 0.036
    soma.gl_hh = 0.0003
    soma.el_hh = -54.3

    dend.insert('hh')
    dend.gnabar_hh = 0.052   
    dend.gkbar_hh = 0.005
    dend.gl_hh = 0.0003
    dend.el_hh = -54.3

    dend.insert('ca_hva')
    dend.insert('cad')
    
    for seg in dend:
        seg.tau_cad = 50
        if seg.x > 0.5:
            seg.gbar_ca_hva = 0.01
        else:
            seg.gbar_ca_hva = 0
            
    return soma, dend

def setup_synapses(dend, direction, dt_stim, syn_weight):

    weights = [syn_weight] * 5
    return setup_synapses_weighted(dend, direction, dt_stim, weights)

def setup_synapses_weighted(dend, direction, dt_stim, weights):

    syns = []
    netstims = []
    ncs = []

    locs = [1.0, 0.8, 0.6, 0.4, 0.2] 

    latencies = [12, 9, 6, 3, 0]
    
    start_time = 20
    
    for i in range(5):
        syn = h.Exp2Syn(dend(locs[i]))
        syn.tau1 = 1; syn.tau2 = 30; syn.e = 0
        syns.append(syn)

        if direction == 'preferred':
            # A->B->C->D->E
            stim_onset = start_time + i * dt_stim
        else:
            # E->D->C->B->A 
            stim_onset = start_time + (4 - i) * dt_stim

        ns = h.NetStim()
        ns.number = 1
        ns.start = stim_onset
        ns.noise = 0
        netstims.append(ns)
        
        nc = h.NetCon(ns, syn)
        nc.weight[0] = weights[i]
        nc.delay = latencies[i]  
        ncs.append(nc)
        
    return syns, netstims, ncs

# 1
def run_speed_tuning(soma, dend):
    dt_list = [1, 2, 3, 4, 5, 6, 8, 10]
    spike_counts = []
    
    for dt in dt_list:
        syns, nss, ncs = setup_synapses(dend, 'preferred', dt, syn_weight=0.0014)
        
        ap_count = h.APCount(soma(0.5))
        ap_count.thresh = 0
        
        h.t = 0; h.v_init = -70; h.celsius = 30; h.tstop = 100
        h.run()
        
        spike_counts.append(ap_count.n)
        
    plt.figure(figsize=(8, 5))
    plt.plot(dt_list, spike_counts, 'o-', linewidth=2, color='navy')
    plt.axvline(x=3, color='r', linestyle='--', label='Theoretical Optimal (3ms)')
    plt.xlabel('Stimulus Interval (ms)')
    plt.ylabel('Soma Spike Count')
    plt.title('Experiment 1: Speed Tuning Curve')
    plt.legend(); plt.grid(True)
    plt.savefig('exp1_speed_tuning.png')

# 2
def run_direction_test(soma, dend):
    optimal_dt = 3 
    
    # pref
    syns1, nss1, ncs1 = setup_synapses(dend, 'preferred', optimal_dt, syn_weight=0.0014)
    t_vec = h.Vector().record(h._ref_t)
    v_soma_p = h.Vector().record(soma(0.5)._ref_v)
    ca_dend_p = h.Vector().record(dend(1.0)._ref_cai)
    
    h.t = 0; h.v_init = -70; h.celsius = 30; h.tstop = 100
    h.run()
    # null
    del syns1, nss1, ncs1 
    syns2, nss2, ncs2 = setup_synapses(dend, 'null', optimal_dt, syn_weight=0.0014)
    v_soma_n = h.Vector().record(soma(0.5)._ref_v)
    ca_dend_n = h.Vector().record(dend(1.0)._ref_cai)
    
    h.t = 0; h.v_init = -70; h.celsius = 30; h.tstop = 100
    h.run()
    t = np.array(t_vec)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    
    ax1.plot(t, v_soma_p, 'k', label='Preferred')
    ax1.plot(t, v_soma_n, 'gray', linestyle='--', label='Null')
    ax1.set_ylabel('Soma V (mV)'); ax1.legend(); ax1.grid(True)
    
    ax2.plot(t, ca_dend_p, 'r', linewidth=2, label='Preferred (Ca spike)')
    ax2.plot(t, ca_dend_n, 'b', linestyle=':', label='Null (Flat)')
    ax2.set_ylabel('[Ca2+] (mM)'); ax2.legend(); ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig('exp2_direction_selectivity.png')
# 3
def run_mechanism_proof(soma, dend):
# normal
    syns, nss, ncs = setup_synapses(dend, 'preferred', dt_stim=3, syn_weight=0.0014)
    t_vec = h.Vector().record(h._ref_t)
    cai_control = h.Vector().record(dend(1.0)._ref_cai)
    
    h.t = 0; h.v_init = -70; h.celsius = 30; h.tstop = 100
    h.run()
    
    # ttx
    saved_gna = soma.gnabar_hh
    soma.gnabar_hh = 0 # <--- BLOCK AP
    
    cai_ttx = h.Vector().record(dend(1.0)._ref_cai)
    v_soma_ttx = h.Vector().record(soma(0.5)._ref_v)
    
    h.t = 0; h.v_init = -70; h.run()
    
    soma.gnabar_hh = saved_gna
    
    plt.figure(figsize=(10, 8))
    plt.subplot(2,1,1)
    plt.plot(t_vec, v_soma_ttx, 'k--', label='Soma V (TTX)')
    plt.ylabel('mV'); plt.legend(); plt.grid(True)
    plt.title('Soma Blocked (No bAP)')
    
    plt.subplot(2,1,2)
    plt.plot(t_vec, cai_control, 'r', label='Normal (bAP + EPSP)')
    plt.plot(t_vec, cai_ttx, 'k:', label='TTX (No bAP)')
    plt.ylabel('[Ca2+] mM'); plt.legend(); plt.grid(True)
    plt.title('Dendritic Calcium requires bAP')
    
    plt.tight_layout()
    plt.savefig('exp3_mechanism_proof.png')

# 4  4 4
def run_plasticity_experiment(soma, dend):

    initial_w = 0.0012
    ca_threshold = 0.107 
    max_weight = 0.00135
    min_weight = 0.00110
    
    # training
    learning_rate_ltp = 0.00005
    learning_rate_ltd = 0.00005
    
    num_trials = 120 
    current_weights = [initial_w] * 5 
    weight_history = {i: [] for i in range(5)}
    
    ltp_c = 0
    ltd_c = 0

    for trial in range(num_trials):
        direction = random.choice(['preferred', 'null'])
        
        syns, nss, ncs = setup_synapses_weighted(dend, direction, dt_stim=3, weights=current_weights)
        ca_rec = h.Vector().record(dend(1.0)._ref_cai)
        h.t = 0; h.v_init = -70; h.celsius = 30; h.tstop = 100
        h.run()
        
        max_ca = np.array(ca_rec).max()
        is_calcium_spike = (max_ca > ca_threshold)

        if is_calcium_spike: ltp_c += 1
        else: ltd_c += 1
        
        for i in range(5):
            if is_calcium_spike:
                current_weights[i] += learning_rate_ltp
            else:
                current_weights[i] -= learning_rate_ltd

            current_weights[i] = max(min_weight, min(current_weights[i], max_weight))
            weight_history[i].append(current_weights[i])
        del syns, nss, ncs

    plt.figure(figsize=(10, 6))
    colors = ['r', 'g', 'b', 'orange', 'purple']
    for i in range(5):
        plt.plot(weight_history[i], color=colors[i], linewidth=2, alpha=0.8)
    
    plt.title(f'Synaptic Weight Evolution (Dynamic Equilibrium)\nLTP: {ltp_c} | LTD: {ltd_c}')
    plt.xlabel('Trials')
    plt.ylabel('Weight')
    
    plt.ylim(min_weight*0.98, max_weight*1.02)
    plt.axhline(y=initial_w, color='gray', linestyle='--', alpha=0.5, label='Start')
    plt.axhline(y=max_weight, color='k', linestyle=':', alpha=0.5, label='Ceiling')
    plt.axhline(y=min_weight, color='k', linestyle='-.', alpha=0.5, label='Floor')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('exp4_learning_evolution.png')
    
def setup_inhibition(dend, pos=0.1, g_max=0.0):

    inh_syn = h.Exp2Syn(dend(pos))
    inh_syn.tau1 = 0.5
    inh_syn.tau2 = 10
    inh_syn.e = -80 
    
    stim = h.NetStim()
    stim.number = 1000 
    stim.interval = 5
    stim.start = 0
    stim.noise = 1
    
    nc = h.NetCon(stim, inh_syn)
    nc.weight[0] = g_max 
    
    return inh_syn, stim, nc

# 5
def run_risk_aversion_experiment(dend, soma):

    reward_levels = np.linspace(0.0005, 0.0030, 20) 
    risk_levels = [0, 0.002] 
    
    results = {}

    plt.figure(figsize=(8, 6))
    colors = ['green', 'red']
    labels = ['Safe Context (Low Risk)', 'Dangerous Context (High Risk)']

    for i, risk_g in enumerate(risk_levels):
        ca_peaks = []
        inh, stim, nc = setup_inhibition(dend, pos=0.1, g_max=risk_g)
        
        for w in reward_levels:
            syns, nss, ncs = setup_synapses_weighted(dend, 'preferred', dt_stim=3, weights=[w]*5)
            
            ca_rec = h.Vector().record(dend(1.0)._ref_cai)
            
            h.t = 0; h.v_init = -70; h.celsius = 30; h.tstop = 100
            h.run()
            
            ca_peaks.append(np.array(ca_rec).max())
            del syns, nss, ncs
        
        results[labels[i]] = ca_peaks
        plt.plot(reward_levels, ca_peaks, 'o-', color=colors[i], label=labels[i], linewidth=2)

        del inh, stim, nc

    plt.axhline(y=0.22, color='k', linestyle=':', label='Decision Threshold (Ca Spike)')
    
    plt.title('Neuronal Utility Function: Impact of Risk (Shunting Inhibition)')
    plt.xlabel('Objective Value (Synaptic Weight / Reward Size)')
    plt.ylabel('Subjective Utility (Dendritic Ca2+ Peak)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.text(0.0010, 0.5, "Risk Aversion:\nNeed higher reward\nto trigger decision", 
             color='red', fontsize=10, bbox=dict(facecolor='white', alpha=0.8))
    
    plt.savefig('exp5_risk_aversion.png')

if __name__ == '__main__':
    my_soma, my_dend = build_model()

    run_speed_tuning(my_soma, my_dend)
    run_direction_test(my_soma, my_dend)
    run_mechanism_proof(my_soma, my_dend)
    run_plasticity_experiment(my_soma, my_dend) 
    run_risk_aversion_experiment(my_dend, my_soma)
    
    print("Finished")