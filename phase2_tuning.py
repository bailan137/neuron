from neuron import h

# 加载机制
h.load_file('stdrun.hoc')
try:
    h.nrn_load_dll('./x86_64/.libs/libnrnmech.so') 
except:
    pass

# 构建模型过程与phase 1完全相同，验证过了可行性
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
dend.gkbar_hh = 0.005
dend.gl_hh = 0.0003
dend.el_hh = -54.3
dend.insert('ca_hva')
dend.insert('cad')

stim_soma = h.IClamp(soma(0.5))
stim_soma.dur = 5; stim_soma.delay = 15

# 树突末端突触输入
syn = h.Exp2Syn(dend(1.0)) 
syn.tau1 = 1; syn.tau2 = 30; syn.e = 0

netstim = h.NetStim()
netstim.number = 1; netstim.start = 15; netstim.noise = 0

nc = h.NetCon(netstim, syn)

# 更新钠通道密度和钙通道密度，直到找到最好的
def update_params(dend_na, ca_bar):
    dend.gnabar_hh = dend_na
    for seg in dend:
        seg.tau_cad = 50
        if seg.x > 0.5:
            seg.gbar_ca_hva = ca_bar
        else:
            seg.gbar_ca_hva = 0

# 运行一次
def run_trial(syn_weight, mode):
    h.t = 0
    h.v_init = -70
    h.celsius = 30
    h.tstop = 60
    # 只开bap ： bap-only
    if mode in ['bAP_only', 'both']:
        stim_soma.amp = 1.0
    else:
        stim_soma.amp = 0
    # 只开syn：syn-only
    if mode in ['syn_only', 'both']:
        nc.weight[0] = syn_weight
    else:
        nc.weight[0] = 0
        
    cai_dend = h.Vector().record(dend(1.0)._ref_cai)
    h.run()
    return cai_dend.max()

# 写个flag
aaa = False

na_range = [0.052, 0.054, 0.055, 0.056, 0.058]

weight_range = [0.0012, 0.0014, 0.0016, 0.0018]

for test_na in na_range:
    update_params(dend_na=test_na, ca_bar=0.01) 
    
    for test_weight in weight_range:
        # ca_both = run_trial(test_weight)
        ca_syn = run_trial(test_weight, 'syn_only')
        ca_bap = run_trial(test_weight, 'bAP_only')
        ca_both = run_trial(test_weight, 'both')
        print(ca_syn)
        print(ca_bap)
        print(ca_both)

        baseline = max(ca_syn, ca_bap)
        if baseline < 1e-6: baseline = 1e-6
        gain = ca_both / baseline

        # 单独刺激不起效
        single_safe = (ca_syn < 0.01 and ca_bap < 0.01)
        # 结合后起效
        both_spike = (ca_both > 0.02)
        # 爆炸
        has_gain = (gain > 2.0)
        
        if single_safe and both_spike and has_gain:
            aaa = True

        if aaa:
            break
    if aaa:
        break

if aaa:
    print("Finished")
    print(f"Dend_Na:{test_na}")
    print(f"Syn_W:{test_weight}")
else:
    print("调整一下范围，没找到")