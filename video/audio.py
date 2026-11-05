import numpy as np, wave
SR=44100; T=30.0; N=int(SR*T); out=np.zeros((N,2))
bpm=120; beat=60/bpm
rng=np.random.default_rng(3)
def add(sig,t0,gain=1.0,pan=0.0):
    i=int(t0*SR); j=min(N,i+len(sig))
    if i>=N: return
    s=sig[:j-i]*gain
    out[i:j,0]+=s*(1-max(0,pan)); out[i:j,1]+=s*(1+min(0,pan))
def tt(d): return np.arange(int(d*SR))/SR
def kick():
    t=tt(0.45); f=45+110*np.exp(-t*30); ph=2*np.pi*np.cumsum(f)/SR
    return np.sin(ph)*np.exp(-t*7)*1.0 + np.random.randn(len(t))*np.exp(-t*200)*0.15
def clap():
    t=tt(0.25); n=rng.standard_normal(len(t))
    env=np.exp(-t*22)+0.6*np.exp(-np.maximum(0,t-0.012)*40)*(t>0.012)
    n=np.convolve(n,[1,-0.9],'same')
    return n*env*0.35
def hat(open_=False):
    t=tt(0.18 if open_ else 0.05); n=rng.standard_normal(len(t)); n=np.diff(np.concatenate([[0],n]))
    return n*np.exp(-t*(18 if open_ else 90))*0.12
def note(f,d,kind='saw',det=0.0):
    t=tt(d); s=np.zeros(len(t))
    for dd in ([-det,0,det] if det else [0]):
        ff=f*(1+dd)
        if kind=='saw': s+=2*((t*ff)%1)-1
        elif kind=='sq': s+=np.sign(np.sin(2*np.pi*ff*t))
        else: s+=np.sin(2*np.pi*ff*t)
    return s
def lp(s,a):
    y=np.zeros_like(s); acc=0.0
    # vectorized one-pole via lfilter-like loop on chunks
    from math import exp
    for i in range(len(s)): acc+=a*(s[i]-acc); y[i]=acc
    return y
def midi(m): return 440*2**((m-69)/12)
def adsr(n,a,r):
    e=np.ones(n); ai=int(a*SR); ri=int(r*SR)
    if ai: e[:ai]=np.linspace(0,1,ai)
    if ri: e[-ri:]*=np.linspace(1,0,ri)
    return e
# chords: Am F C G (each 2s = 4 beats), loop
prog=[[57,60,64],[53,57,60],[48,52,55],[55,59,62]]
roots=[45,41,48,43]
drop=3.8
# pad
for b in range(15):
    ch=prog[b%4]; t0=b*2.0
    s=sum(note(midi(m+12),2.05,'saw',0.004) for m in ch)/3
    s=lp(s,0.04)*adsr(len(s),0.25,0.4)
    add(s,t0,0.11 if t0<drop else 0.09,0)
# bass + arps after drop
for b in range(int(drop/beat), int(29.0/beat)):
    t0=b*beat; ci=int(t0//2)%4
    for k in range(2):
        s=note(midi(roots[ci]),beat/2*0.9,'sq'); s=lp(s,0.08)*adsr(len(s),0.005,0.05)
        add(s,t0+k*beat/2,0.16)
    # arp 16ths
    ch=prog[ci]
    for k in range(4):
        m=ch[(b*4+k)%3]+24
        s=note(midi(m),beat/4*0.8,'saw',0.003); s=lp(s,0.25)*np.exp(-tt(len(s)/SR)*14)
        add(s,t0+k*beat/4,0.05,0.4 if k%2 else -0.4)
# drums
for b in range(int(drop/beat), int(29.0/beat)):
    t0=b*beat
    add(kick(),t0,0.9)
    if b%2==1: add(clap(),t0,1.0)
    add(hat(),t0+beat/2,1.0,0.3); add(hat(),t0+beat/4,0.5,-0.3); add(hat(),t0+3*beat/4,0.5,-0.3)
    if b%4==3: add(hat(True),t0+beat/2,1.0)
# intro taps on logo beats
for t0 in [0.15,0.55,0.95]: add(kick(),t0,0.5)
# riser before drop
def riser(d):
    t=tt(d); n=rng.standard_normal(len(t))
    y=np.zeros_like(n); acc=0
    cut=0.01+0.4*(t/d)**2
    for i in range(len(n)): acc+=cut[i]*(n[i]-acc); y[i]=acc
    return y*(t/d)**1.5*0.5
add(riser(1.6),drop-1.6,0.8)
def impact():
    t=tt(1.6); f=55*np.exp(-t*1.5)+30
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*2.5)+rng.standard_normal(len(t))*np.exp(-t*8)*0.3
add(impact(),drop,0.9); add(impact(),25.35,0.8); add(impact(),29.0,0.7)
def whoosh(d=0.7):
    t=tt(d); n=rng.standard_normal(len(t)); env=np.sin(np.pi*t/d)**2
    y=np.zeros_like(n); acc=0; cut=0.02+0.25*np.sin(np.pi*t/d)
    for i in range(len(n)): acc+=cut[i]*(n[i]-acc); y[i]=acc
    return y*env*0.9
for w in [5.6,9.45,18.4,24.4]: add(whoosh(),w,0.9,0.0)
# typing ticks
for i in range(19): add(hat(),27.1+i*(1.1/19),0.9)
# pops for features
for i in range(4):
    s=note(midi(76+i*2),0.12,'sine')*np.exp(-tt(0.12)*30); add(s,10.8+i*1.55,0.25)
# master
fade=np.ones(N); fi=int(29.3*SR); fade[fi:]=np.linspace(1,0,N-fi)
out*=fade[:,None]
out=np.tanh(out*1.3)/np.tanh(1.3)
out/=np.max(np.abs(out))*1.12
w=wave.open('music.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((out*32767).astype('<i2').tobytes()); w.close()
print('ok')
