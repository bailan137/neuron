import os
import matplotlib.pyplot as plt
import numpy as np
import random
from neuron import h, gui

def initialize_neuron_env():
    h.load_file('stdrun.hoc')
    if os.path.exists('./x86_64/.libs/libnrnmech.so'):
        h.nrn_load_dll('./x86_64/.libs/libnrnmech.so') 
    else:
        print("Warning")

def build_model():
    soma = h.Section(name='soma'); dend = h.Section(name='dend')
    dend.connect(soma(1)); soma.L, soma.diam = 20, 20
    dend.L, dend.diam, dend.nseg = 500, 2, 51
    for sec in h.allsec(): sec.Ra, sec.cm = 150, 1
    soma.insert('hh'); dend.insert('hh')
    dend.gnabar_hh = 0.052
    dend.insert('ca_hva'); dend.insert('cad')
    for seg in dend:
        seg.tau_cad = 50
        seg.gbar_ca_hva = 0.01 if seg.x > 0.5 else 0
    return soma, dend

def setup_single_stim(dend, pos, time, weight):
    syn = h.Exp2Syn(dend(pos)); syn.tau1, syn.tau2 = 1, 20
    ns = h.NetStim(); ns.number, ns.start, ns.noise = 1, time, 0
    nc = h.NetCon(ns, syn); nc.weight[0], nc.delay = weight, 0
    return syn, ns, nc

def calculate_rpe_signal(soma, dend, confidence, is_correct):
    soma_voltage = -70 + 25 * confidence
    dend_weight = 0.005 if is_correct else 0.0
    
    v_clamp = h.SEClamp(soma(0.5))
    v_clamp.dur1, v_clamp.amp1, v_clamp.rs = 100, soma_voltage, 1e-3
    syn, ns, nc = setup_single_stim(dend, pos=0.8, time=40, weight=dend_weight)
    
    rec_v_dend_prox = h.Vector().record(dend(0.01)._ref_v)
    h.t, h.v_init, h.dt, h.tstop = 0, -70, 0.025, 100
    h.run()
    
    rpe_proxy = np.array(rec_v_dend_prox) - soma_voltage
    if len(rpe_proxy) < int(50/h.dt): return 0.0
    peak_rpe = np.max(rpe_proxy[int(41/h.dt):int(50/h.dt)])
    
    del v_clamp, syn, ns, nc
    return peak_rpe

class SimpleAgent:
    def __init__(self):
        self.possible_rules = ["add_one", "multiply_by_two", "square_the_number"]
        self.current_rule = "add_one"
        self.confidence = 0.8 

    def predict(self, input_number):
        if self.current_rule == "add_one":
            return input_number + 1
        elif self.current_rule == "multiply_by_two":
            return input_number * 2
        elif self.current_rule == "square_the_number":
            return input_number * input_number
    
    def learn(self, rpe_signal):
        error_threshold = -1.0 
        
        if rpe_signal < error_threshold:
            old_rule = self.current_rule
            while self.current_rule == old_rule:
                self.current_rule = random.choice(self.possible_rules)
            self.confidence = 0.4 
        elif rpe_signal > 0:
            self.confidence = min(1.0, self.confidence + 0.1)
        else:
            self.confidence = min(1.0, self.confidence + 0.05)

def run_simple_agent_loop():
    initialize_neuron_env()
    neuron_soma, neuron_dend = build_model()
    agent = SimpleAgent()
    
    world_rule = lambda x: x * 2
    num_trials = 70
    rpe_history = []

    for i in range(num_trials):
        print("\n" + "="*20 + f" Trial {i+1} " + "="*20)

        input_number = random.randint(2, 10)
        prediction = agent.predict(input_number)
        confidence = agent.confidence

        correct_answer = world_rule(input_number)
        is_correct = (prediction == correct_answer)

        rpe_signal = calculate_rpe_signal(neuron_soma, neuron_dend, confidence, is_correct)
        rpe_history.append(rpe_signal)
        agent.learn(rpe_signal)
            
    plt.figure(figsize=(10, 6))
    steps = np.arange(1, num_trials + 1)
    colors = ['green' if rpe > -0.5 else 'red' for rpe in rpe_history]
    
    plt.bar(steps, rpe_history, color=colors, alpha=0.7, label='RPE Signal')
    plt.axhline(0, color='k', linestyle='--', label='Zero Error Baseline')
    
    plt.title("RPE-Guided Rule Learning in a Simple Agent")
    plt.xlabel("Trial Number")
    plt.ylabel("Peak RPE Signal (V_dend - V_soma) [mV]")
    plt.xticks(steps)
    plt.legend()
    plt.grid(True, axis='y', linestyle='--', alpha=0.6)
    
    plt.savefig("simple_agent_neuron_loop.png")

if __name__ == '__main__':
    if not os.path.exists('./x86_64'):
        print("MOD files not compiled. Compiling now...")
        os.system('nrnivmodl')
        
    run_simple_agent_loop()