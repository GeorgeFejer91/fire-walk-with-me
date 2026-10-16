#!/usr/bin/env python3
"""Original, non-melodic analog-synth login cue. No samples or quoted melody."""
from array import array
import json
import math
from pathlib import Path
import wave

RATE, DURATION = 48000, 6.4

def render(path):
    count = round(RATE * DURATION)
    dry = array('d')
    for i in range(count):
        t = i / RATE
        attack = (1 - math.exp(-t / .34)) ** 2
        release = min(1, max(0, (DURATION - t) / 2.0)) ** 2
        bass_env = attack * release * math.exp(-t / 3.4)
        # A low pedal and its audible harmonics give small speakers some body.
        bass = sum(weight * math.sin(2 * math.pi * 55 * harmonic * t)
                   for harmonic, weight in [(1,.42),(2,.26),(3,.10),(4,.04)])
        pad = 0.0
        for frequency, phase in [(164.814,.4),(220.0,1.2),(246.942,.8),(261.626,2.1)]:
            pad += .042 * (math.sin(2*math.pi*frequency*t + phase)
                           + .5*math.sin(2*math.pi*frequency*1.0016*t + phase))
        pad_env = (1-math.exp(-t/.9))*release*math.exp(-max(0,t-2.1)/2.7)
        bell = .022 * math.sin(2*math.pi*659.255*t + .6*math.sin(2*math.pi*1318.51*t)) * math.exp(-t/1.1)
        dry.append((bass*bass_env + pad*pad_env + bell*attack)*release)
    stereo = array('d')
    delays = [(int(RATE*.137),.13),(int(RATE*.283),.085),(int(RATE*.421),.05)]
    for i, value in enumerate(dry):
        tail = sum(dry[i-delay]*gain for delay,gain in delays if i>=delay)
        fade = min(1, (count-1-i)/(RATE*.3)) if i>count-RATE*.3 else 1
        stereo.extend([(value+tail)*fade,(value+tail*.88)*fade])
    peak = max(abs(x) for x in stereo)
    gain = .5 / peak
    pcm = array('h',(round(max(-1,min(1,x*gain))*32767) for x in stereo))
    if __import__('sys').byteorder != 'little': pcm.byteswap()
    path.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(path),'wb') as output:
        output.setnchannels(2);output.setsampwidth(2);output.setframerate(RATE)
        output.writeframes(pcm.tobytes())
    assert max(abs(x) for x in pcm)<=16384
    assert pcm[0]==pcm[1]==pcm[-1]==pcm[-2]==0
    rms = math.sqrt(sum((x/32768)**2 for x in pcm)/len(pcm))
    report={'seconds':DURATION,'sample_rate':RATE,'channels':2,
            'peak_dbfs':20*math.log10(max(abs(x) for x in pcm)/32768),
            'rms_dbfs':20*math.log10(rms),'composition':'Original sustained pedal and chord; no borrowed melody or samples.'}
    path.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Rendered original login cue:',path)
    return report

if __name__=='__main__':
    render(Path(__file__).resolve().parents[1]/'assets/audio/into-the-lodge.wav')
