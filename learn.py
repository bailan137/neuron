import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import random
import sys 
from neuron import h, gui

def initialize_neuron_env():
    h.load_file('stdrun.hoc')
    lib_path = './x86_64/libnrnmech.so' 

    if os.path.exists(lib_path):
        try:
            h.nrn_load_dll(lib_path) 
        except RuntimeError as e:
            if "The user defined name already exists" in str(e):
                print("NEURON mechanisms already loaded (detected by RuntimeError: mechanism name already exists). Proceeding.")
            else:
                print(f"CRITICAL ERROR: Failed to load NEURON DLL due to unexpected RuntimeError: {e}")
                sys.exit(1)

    else:
        print("Warning: Could not find NMODL mechanisms at expected path. Attempting to compile...")
        if os.system('nrnivmodl') != 0:
            print("CRITICAL ERROR: nrnivmodl compilation command failed. Exiting.")
            sys.exit(1)
        if os.path.exists(lib_path):
            try:
                h.nrn_load_dll(lib_path)
                print("NEURON mechanisms compiled and loaded successfully.")
            except RuntimeError as e:
                if "The user defined name already exists" in str(e):
                    print("NEURON mechanisms already loaded after compilation (detected by RuntimeError). Proceeding.")
                else:
                    print(f"CRITICAL ERROR: Failed to load NEURON DLL due to unexpected RuntimeError: {e}")
                    sys.exit(1)
        else:
            print(f"CRITICAL ERROR: Compilation succeeded but could not find mechanisms at {lib_path}. Exiting.")
            sys.exit(1)
def build_model():
    soma = h.Section(name='soma'); dend = h.Section(name='dend')
    dend.connect(soma(1)); soma.L, soma.diam = 20, 20
    dend.L, dend.diam, dend.nseg = 500, 2, 51
    for sec in h.allsec(): 
        sec.Ra, sec.cm = 150, 1
        
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
    time_points_for_check = int(50/h.dt)
    if len(rpe_proxy) < time_points_for_check: 
        print("WARNING")
        return 0.0
    start_idx = int(41/h.dt)
    end_idx = int(50/h.dt)
    peak_rpe = np.max(rpe_proxy[start_idx:end_idx])
    del v_clamp, syn, ns, nc
    
    return peak_rpe
class BaseAgent:
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

class RPE_Agent(BaseAgent):
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


class Binary_Agent(BaseAgent):
    def learn(self, is_correct):
        if not is_correct:
            if self.confidence > 0.7:
                old_rule = self.current_rule
                while self.current_rule == old_rule:
                    self.current_rule = random.choice(self.possible_rules)
                self.confidence = 0.4 
            else:
                print("  - Agent Learning (Binary): Wrong, but was not confident. Trying again.")
        else:
            self.confidence = min(1.0, self.confidence + 0.1)

def run_loop(agent_type, soma_sec, dend_sec):
    if agent_type == 'rpe':
        agent = RPE_Agent()
    elif agent_type == 'binary':
        agent = Binary_Agent()
    else:
        raise ValueError("Unknown agent type. Choose 'rpe' or 'binary'.")
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

        rpe_signal = calculate_rpe_signal(soma_sec, dend_sec, confidence, is_correct)
        rpe_history.append(rpe_signal)
        if agent_type == 'rpe':
            agent.learn(rpe_signal)
        elif agent_type == 'binary':
            agent.learn(is_correct)
    plt.figure(figsize=(12, 7))
    steps = np.arange(1, num_trials + 1)
    colors = ['#2ca02c' if rpe > -0.5 else '#d62728' for rpe in rpe_history]
    
    plt.bar(steps, rpe_history, color=colors, alpha=0.8, label='RPE Signal')
    plt.axhline(0, color='black', linestyle='--', linewidth=1, label='Zero Error Baseline')
    plt.axhline(-1.0, color='red', linestyle=':', linewidth=1, label='RPE Switching Threshold')
    
    title = f"RPE-Guided Rule Learning ({agent_type.upper()} Agent)"
    plt.title(title, fontsize=16)
    plt.xlabel("Trial Number", fontsize=12)
    plt.ylabel("Peak RPE Signal (V_dend - V_soma) [mV]", fontsize=12)
    if num_trials <= 20:
        plt.xticks(steps)
    else:
        plt.xticks(np.arange(0, num_trials + 1, 5))

    plt.legend()
    plt.grid(True, axis='y', linestyle='--', alpha=0.6)
    plt.tight_layout()
    
    output_filename = f"learning_curve_{agent_type}_agent.png"
    plt.savefig(output_filename)

if __name__ == '__main__':
    if not os.path.exists('./x86_64'):
        print("MOD files not compiled. Compiling now...")
        os.system('nrnivmodl')
    try:
        initialize_neuron_env()
    except Exception as e:
        print(f"\nFATAL: NEURON initialization failed: {e}")
        sys.exit(1)
    neuron_soma, neuron_dend = build_model()
    

    run_loop(agent_type='rpe', soma_sec=neuron_soma, dend_sec=neuron_dend)
    run_loop(agent_type='binary', soma_sec=neuron_soma, dend_sec=neuron_dend)
    