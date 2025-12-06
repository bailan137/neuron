from neuron import h
import matplotlib.pyplot as plt
import numpy as np

# 直接按phase 1 中验证的可行方式构建，并且把phase 2的参数导进去
h.load_file('stdrun.hoc')
try:
    h.nrn_load_dll('./x86_64/.libs/libnrnmech.so') 
except:
    pass
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

# build 突触
def setup_synapses(dend, direction, dt_stim, syn_weight):
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
            stim_onset = start_time + i * dt_stim
        else:
            stim_onset = start_time + (4 - i) * dt_stim
            
        ns = h.NetStim()
        ns.number = 1
        ns.start = stim_onset
        ns.noise = 0
        netstims.append(ns)
        
        nc = h.NetCon(ns, syn)
        nc.weight[0] = syn_weight 
        nc.delay = latencies[i]
        ncs.append(nc)
        
    return syns, netstims, ncs

# experiment 1 speed
def run_speed_tuning(soma, dend):
    print("Experiment 1")
    dt_list = [1, 2, 3, 4, 5, 6, 8, 10]
    spike_counts = []
    
    for dt in dt_list:
        syns, nss, ncs = setup_synapses(dend, 'preferred', dt, syn_weight=0.0014)
        print(syns,nss,ncs)
        ap_count = h.APCount(soma(0.5))
        ap_count.thresh = 0
        
        h.t = 0; h.v_init = -70; h.celsius = 30; h.tstop = 100
        h.run()
        
        count = ap_count.n
        spike_counts.append(count)
        print(spike_counts)
        
    plt.figure(figsize=(8, 5))
    plt.plot(dt_list, spike_counts, 'o-', linewidth=2, color='navy')
    plt.axvline(x=3, color='r', linestyle='--', label='Theoretical Optimal (3ms)')
    plt.xlabel('Stimulus Interval (ms) [Inverse of Speed]')
    plt.ylabel('Soma Spike Count')
    plt.title('Experiment 1: Speed Tuning Curve')
    plt.legend()
    plt.grid(True)
    plt.savefig('exp1_speed_tuning.png')

# experiment 2 : direction -- 看看是不是突触强度导致方向选择性
def run_direction_test(soma, dend):
    optimal_dt = 3 
    # pre
    syns1, nss1, ncs1 = setup_synapses(dend, 'preferred', optimal_dt, syn_weight=0.0014)
    
    t_vec = h.Vector().record(h._ref_t)
    v_soma_pref = h.Vector().record(soma(0.5)._ref_v)
    ca_dend_pref = h.Vector().record(dend(1.0)._ref_cai)
    
    h.t = 0; h.v_init = -70; h.celsius = 30; h.tstop = 100
    h.run()
    
    t = np.array(t_vec)
    vs_p = np.array(v_soma_pref)
    ca_p = np.array(ca_dend_pref)
    print(ca_p.max())
    del syns1, nss1, ncs1 
    # null
    syns2, nss2, ncs2 = setup_synapses(dend, 'null', optimal_dt, syn_weight=0.0014)
    
    v_soma_null = h.Vector().record(soma(0.5)._ref_v)
    ca_dend_null = h.Vector().record(dend(1.0)._ref_cai)
    
    h.t = 0; h.v_init = -70; h.celsius = 30; h.tstop = 100
    h.run()
    
    vs_n = np.array(v_soma_null)
    ca_n = np.array(ca_dend_null)
    print(ca_n.max())

    denom = ca_p.max() + ca_n.max()
    if denom == 0: denom = 1e-9
    dsi_ca = (ca_p.max() - ca_n.max()) / denom
    print(dsi_ca)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    ax1.plot(t, vs_p, 'k', label='Preferred')
    ax1.plot(t, vs_n, 'gray', linestyle='--', label='Null')
    ax1.set_ylabel('Soma V (mV)')
    ax1.legend()
    ax1.grid(True)
    
    ax2.plot(t, ca_p, 'r', linewidth=2, label='Preferred (Ca spike)')
    ax2.plot(t, ca_n, 'b', linestyle=':', label='Null (Flat)')
    ax2.set_ylabel('Dend [Ca2+] (mM)')
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig('exp2_direction_selectivity.png')

# experiment 3：依赖bap实验
def run_mechanism_proof(soma, dend):

    t_vec = h.Vector().record(h._ref_t)
    cai_control = h.Vector().record(dend(1.0)._ref_cai) # normal
    cai_ttx = h.Vector().record(dend(1.0)._ref_cai)     # ttx
    v_soma_ttx = h.Vector().record(soma(0.5)._ref_v) 

    # normal
    syns, nss, ncs = setup_synapses(dend, 'preferred', dt_stim=3, syn_weight=0.0014)

    h.t = 0; h.v_init = -70; h.celsius = 30; h.tstop = 100
    h.run()
    cai_control_data = np.array(cai_control)

    # ttx
    saved_gnabar = soma.gnabar_hh
    soma.gnabar_hh = 0 

    h.t = 0; h.v_init = -70
    h.run()
    cai_ttx_data = np.array(cai_ttx)
    v_soma_ttx_data = np.array(v_soma_ttx)

    soma.gnabar_hh = saved_gnabar

    plt.figure(figsize=(10, 8))
    plt.subplot(2, 1, 1)
    plt.plot(t_vec, v_soma_ttx_data, 'k--', label='Soma V (with TTX)')
    plt.title('Control Experiment: Blocking Somatic Spikes (TTX)')
    plt.ylabel('Voltage (mV)')
    plt.legend()
    plt.grid(True)
    plt.subplot(2, 1, 2)
    plt.plot(t_vec, cai_control_data, 'r-', linewidth=2, label='Normal (Preferred Dir)')
    plt.plot(t_vec, cai_ttx_data, 'k:', linewidth=2, label='TTX (No bAP)')
    plt.title('Dendritic Calcium: bAP Dependency')
    plt.xlabel('Time (ms)')
    plt.ylabel('[Ca2+] (mM)')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig('exp3_mechanism_proof.png')

import numpy as np

# experiment 4：噪声鲁棒
def run_jitter_test(soma, dend):
    
    sigma_list = [0, 1, 2, 3, 5]
    dsi_list = []
    
    for sigma in sigma_list:
        syns1, nss1, ncs1 = setup_synapses(dend, 'preferred', dt_stim=3, syn_weight=0.0014)
        
        for ns in nss1:
            noise_val = np.random.normal(0, sigma)
            ns.start += noise_val
            
        h.t = 0; h.v_init = -70; h.run()
        ca_p = h.Vector().record(dend(1.0)._ref_cai); h.run()
        peak_p = np.array(ca_p).max()
        
        # null
        syns2, nss2, ncs2 = setup_synapses(dend, 'null', dt_stim=3, syn_weight=0.0014)
        for ns in nss2:
            ns.start += np.random.normal(0, sigma)
            
        h.t = 0; h.v_init = -70; h.run()
        ca_n = h.Vector().record(dend(1.0)._ref_cai); h.run()
        peak_n = np.array(ca_n).max()
        
        denom = peak_p + peak_n
        if denom < 1e-9: denom = 1e-9
        dsi = (peak_p - peak_n) / denom
        dsi_list.append(dsi)
        
        print(sigma,dsi)

    # Plot
    plt.figure()
    plt.plot(sigma_list, dsi_list, 'o-', color='purple')
    plt.title('Robustness: DSI vs Input Jitter')
    plt.xlabel('Jitter Sigma (ms)')
    plt.ylabel('Direction Selectivity Index')
    plt.grid(True)
    plt.savefig('exp4_jitter.png')

# experiment 5
def run_attention_test(soma, dend):
  
    states = {'High Attention': 0.01, 'Low Attention': 0.004}
    results = {}
    
    for name, g_ca in states.items():
        # 修改模型参数
        for seg in dend:
            if seg.x > 0.5: seg.gbar_ca_hva = g_ca
        
        # pref
        syns, nss, ncs = setup_synapses(dend, 'preferred', dt_stim=3, syn_weight=0.0014)
        v_dend = h.Vector().record(dend(1.0)._ref_v)
        t_vec = h.Vector().record(h._ref_t)
        
        h.t = 0; h.v_init = -70; h.run()
        results[name] = (np.array(t_vec), np.array(v_dend))
        
    # Plot
    plt.figure()
    for name, (t, v) in results.items():
        plt.plot(t, v, label=name, linewidth=2)
    plt.title('Effect of Attention (Ca_Channel Modulation)')
    plt.xlabel('Time (ms)')
    plt.ylabel('Dendrite Voltage (mV)')
    plt.legend()
    plt.grid(True)
    plt.savefig('exp5_attention.png')
    
    for seg in dend:
        if seg.x > 0.5: seg.gbar_ca_hva = 0.01

# experiment 6: moni 强化学习

def run_secondary_conditioning(soma, dend):  

    def update_weight(w, coincident_detected):
        learning_rate = 0.0002
        if coincident_detected:
            return min(w + learning_rate, 0.004) 
        else:
            return max(w - 0.00001, 0.0)
    
    w_CS1 = 0.0001 
    w_CS2 = 0.0001 
    
    history_w1 = []
    history_w2 = []
    

    # CS1 -- reward

    objects_phase1 = [] 

    for trial in range(30):
        syn1, ns1, nc1 = setup_single_stim(dend, pos=0.4, time=50, weight=w_CS1)
        stim_us = h.IClamp(soma(0.5))
        stim_us.delay = 60
        stim_us.dur = 2
        stim_us.amp = 10
        ap_counter = h.APCount(soma(0.5))
        ap_counter.thresh = 0
        
        objects_phase1.extend([syn1, ns1, nc1, stim_us, ap_counter])

        h.t = 0; h.v_init = -70; h.tstop = 100; h.run()
        
        w_CS1 = update_weight(w_CS1, True) 
        
        history_w1.append(w_CS1)
        history_w2.append(w_CS2)
        
    del objects_phase1 

    # CS 2 --CS1
    
    objects_phase2 = []

    for trial in range(30):
        syn2, ns2, nc2 = setup_single_stim(dend, pos=1.0, time=30, weight=w_CS2) 
        syn1, ns1, nc1 = setup_single_stim(dend, pos=0.4, time=50, weight=w_CS1)

        
        objects_phase2.extend([syn1, ns1, nc1, syn2, ns2, nc2])
        
        ca_rec = h.Vector().record(dend(1.0)._ref_cai)
        h.t = 0; h.v_init = -70; h.tstop = 100; h.run()

        max_ca = np.array(ca_rec).max() if len(ca_rec) > 0 else 0
        coincidence = (max_ca > 0.1)
        print(max_ca)
        print(coincidence)

        w_CS2 = update_weight(w_CS2, coincidence)
        
        w_CS1 = update_weight(w_CS1, True)
        
        history_w1.append(w_CS1)
        history_w2.append(w_CS2)
        
    del objects_phase2

    plt.figure(figsize=(10, 6))
    plt.plot(history_w1, label='CS1 Weight (Proximal)', color='blue', linewidth=2)
    plt.plot(history_w2, label='CS2 Weight (Distal)', color='red', linewidth=2)
    
    plt.axvline(x=29, color='k', linestyle='--', alpha=0.5) 
    plt.text(15, 0.003, "Phase 1:\nCS1 -> Reward", color='blue', ha='center')
    plt.text(45, 0.003, "Phase 2:\nCS2 -> CS1\n(Value Backprop)", color='red', ha='center')
    
    plt.title('Biophysical Implementation of TD Learning (Secondary Conditioning)')
    plt.xlabel('Trials')
    plt.ylabel('Synaptic Weight')
    plt.legend()
    plt.grid(True)
    plt.savefig('exp6_td_learning.png')
    print("✅ 图表已保存: exp6_td_learning.png")

def setup_single_stim(dend, pos, time, weight):
    syn = h.Exp2Syn(dend(pos))
    syn.tau1 = 1; syn.tau2 = 40 
    ns = h.NetStim()
    ns.number=1; ns.start=time; ns.noise=0
    nc = h.NetCon(ns, syn)
    nc.weight[0] = weight
    nc.delay = 0
    return syn, ns, nc


# experiment 7 : 形态学天然预测误差
def run_morphological_rpe_experiment(soma, dend):

    scenarios = [
        {'name': 'Surprise (R>V)', 'v_clamp': -70, 'r_weight': 0.005}, # 无预期 无奖励
        {'name': 'Predicted (R=V)', 'v_clamp': -50, 'r_weight': 0.005}, # 有预期 有奖励
        {'name': 'Disappointment (R<V)', 'v_clamp': -40, 'r_weight': 0.0}   # 大预期 无奖励
    ]
    
    plt.figure(figsize=(10, 6))
    
    for scenario in scenarios:
        stim_pred = h.IClamp(soma(0.5))
        stim_pred.delay = 0
        stim_pred.dur = 100
        v_clamp = h.SEClamp(soma(0.5))
        v_clamp.dur1 = 100
        v_clamp.amp1 = scenario['v_clamp']
        v_clamp.rs = 1e-3

        syn, ns, nc = setup_single_stim(dend, pos=0.8, time=40, weight=scenario['r_weight'])
    
        rec_v_soma = h.Vector().record(soma(0.5)._ref_v)
        rec_v_dend_prox = h.Vector().record(dend(0.01)._ref_v) 
        rec_t = h.Vector().record(h._ref_t)
        
        h.t = 0; h.v_init = -70; h.celsius = 30; h.run()

        rpe_proxy = np.array(rec_v_dend_prox) - np.array(rec_v_soma)
        
        plt.plot(rec_t, rpe_proxy, label=f"{scenario['name']}")
        
        del syn, ns, nc, v_clamp, stim_pred

    plt.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    plt.title('Innovation: Dendritic Axial Current as Reward Prediction Error (RPE)')
    plt.xlabel('Time (ms)')
    plt.ylabel('RPE Proxy (V_dend - V_soma) [mV]')
    plt.legend()
    plt.grid(True)
    plt.text(60, 10, "Surprise (+RPE)\nCurrent -> Soma", color='blue')
    plt.text(60, -10, "Disappointment (-RPE)\nCurrent <- Soma", color='green')
    
    plt.savefig('exp7_morphological_rpe.png')

if __name__ == '__main__':
    my_soma, my_dend = build_model()
    
    run_speed_tuning(my_soma, my_dend)
    run_direction_test(my_soma, my_dend)
    # run_mechanism_proof(my_soma, my_dend) 
    # run_jitter_test(my_soma, my_dend)
    # run_attention_test(my_soma, my_dend)
    run_secondary_conditioning(my_soma, my_dend)
    # run_morphological_rpe_experiment(my_soma, my_dend)