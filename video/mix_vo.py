"""Seslendirmeyi cümlelere böler, sahnelere hizalar, müziği altında kısar (ducking) ve videoya ekler.
Kullanım: python3 mix_vo.py take1.mp3"""
import sys, subprocess, re, numpy as np, wave
src=sys.argv[1]; SR=44100
raw=subprocess.run(['ffmpeg','-v','error','-i',src,'-f','s16le','-ac','1','-ar',str(SR),'-'],capture_output=True).stdout
v=np.frombuffer(raw,'<i2').astype(np.float32)/32768
# cümle aralarını bul
log=subprocess.run(['ffmpeg','-hide_banner','-i',src,'-af','silencedetect=n=-38dB:d=0.22','-f','null','-'],capture_output=True,text=True).stderr
st=[float(x) for x in re.findall(r'silence_start: ([\d.]+)',log)]
en=[float(x) for x in re.findall(r'silence_end: ([\d.]+)',log)]
segs=[];cur=0.0
for s,e in zip(st,en):
    if s-cur>0.15: segs.append((cur,s))
    cur=e
if len(v)/SR-cur>0.15: segs.append((cur,len(v)/SR))
print('bulunan parçalar:',[(round(a,2),round(b,2)) for a,b in segs])
# 7 cümle -> sahne başlangıçları (sn). 4. cümle 4 özellik içeriyorsa birden fazla parçaya bölünmüş olabilir.
targets=[0.45,3.75,6.55,10.7,19.3,20.8,26.9]
groups=[]
if len(segs)==7: groups=[[s] for s in segs]
else:
    # baştan 3, sondan 3 cümle sabit, arası özellik bloğu
    groups=[[segs[0]],[segs[1]],[segs[2]],segs[3:-3],[segs[-3]],[segs[-2]],[segs[-1]]]
N=int(30*SR); vo=np.zeros(N); pos=0
for g,t in zip(groups,targets):
    t=max(t,pos)
    a=int(g[0][0]*SR); b=int(g[-1][1]*SR)
    piece=v[max(0,a-int(.03*SR)):b+int(.08*SR)]
    i=int(t*SR); j=min(N,i+len(piece)); vo[i:j]+=piece[:j-i]; pos=j/SR+0.1
    print(f'{t:5.2f}s -> {j/SR:5.2f}s')
w=wave.open('music.wav'); m=np.frombuffer(w.readframes(w.getnframes()),'<i2').astype(np.float32).reshape(-1,2)/32768
m=m[:N]
env=np.convolve(np.abs(vo),np.ones(2205)/2205,'same'); duck=1-0.6*np.clip(env/0.05,0,1)
duck=np.convolve(duck,np.ones(4410)/4410,'same')
mix=m*duck[:,None]*0.85+vo[:,None]*1.15
mix=np.tanh(mix*1.2)/np.tanh(1.2); mix/=np.abs(mix).max()*1.05
o=wave.open('mix_vo.wav','wb');o.setnchannels(2);o.setsampwidth(2);o.setframerate(SR);o.writeframes((mix*32767).astype('<i2').tobytes());o.close()
subprocess.run(['ffmpeg','-y','-v','error','-i','limitsiz-vip-tanitim.mp4','-i','mix_vo.wav','-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','192k','-shortest','limitsiz-vip-tanitim-seslendirmeli.mp4'],check=True)
print('ok -> limitsiz-vip-tanitim-seslendirmeli.mp4')
