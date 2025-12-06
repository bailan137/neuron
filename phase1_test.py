from neuron import h
import matplotlib.pyplot as plt

h.load_file('stdrun.hoc')

# 定义一个有胞体和树突的模型
soma = h.Section(name='soma')
dend = h.Section(name='dend')
dend.connect(soma(1))
soma.L = 20
soma.diam = 20
dend.L = 500
dend.diam = 1.0   
dend.nseg = 51


for sec in h.allsec():
    sec.Ra = 150
    sec.cm = 1

soma.insert('hh')
soma.gnabar_hh = 0.5   
soma.gkbar_hh = 0.036
soma.gl_hh = 0.0003
soma.el_hh = -54.3


dend.insert('hh')
dend.gnabar_hh = 0.05   
dend.gkbar_hh = 0.01   
dend.gl_hh = 0.0003
dend.el_hh = -54.3

stim = h.IClamp(soma(0.5))
stim.delay = 10
stim.dur = 5
stim.amp = 2.0  

h.v_init = -70
h.celsius = 24  
h.tstop = 50

# 开始运行
t_vec = h.Vector().record(h._ref_t)
v_soma = h.Vector().record(soma(0.5)._ref_v)
v_dend_dist = h.Vector().record(dend(1.0)._ref_v)

h.run()

# 输出结果
soma_peak = v_soma.max()
print(soma_peak)
dend_peak = v_dend_dist.max()
print(dend_peak)

plt.figure(figsize=(10, 6))
plt.plot(t_vec, v_soma, 'k', linewidth=2, label='Soma')
plt.plot(t_vec, v_dend_dist, 'r', linewidth=2, label='Distal Dendrite')
plt.axhline(-25, color='gray', linestyle='--', label='Target Threshold (-25mV)')
plt.title(f'Soma={soma_peak:.1f}, Dend={dend_peak:.1f}')
plt.legend()
plt.grid(True)
plt.savefig('phase1_guaranteed.png')


if soma_peak > 20 and dend_peak > -40:
    print(f"产生正常动作电位{soma_peak},远端有足够强回声{dend_peak}")
else:
    print("Error")