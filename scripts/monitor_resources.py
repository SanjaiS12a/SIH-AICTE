"""Dependency-free observed laptop/container resource samples; not process-attributed GPU data."""
import argparse
import ctypes
from ctypes import wintypes
import json
import subprocess
import time
from pathlib import Path

class Memory(ctypes.Structure):
    _fields_=[('length',wintypes.DWORD),('load',wintypes.DWORD)]+[(n,ctypes.c_ulonglong) for n in ['total','available','page_total','page_available','virtual_total','virtual_available','extended']]

def ticks():
    values=[wintypes.FILETIME() for _ in range(3)]
    if not ctypes.windll.kernel32.GetSystemTimes(*(ctypes.byref(v) for v in values)):raise OSError('GetSystemTimes failed')
    return [v.dwHighDateTime*2**32+v.dwLowDateTime for v in values]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--seconds',type=int,default=180);parser.add_argument('--label',choices=['initial','100000'],default='initial');args=parser.parse_args()
    if not 1<=args.seconds<=3600:raise ValueError('Bound the sampler to 1–3600 seconds')
    dest=Path(__file__).resolve().parents[1]/f'tests/results/completion-resources-{args.label}.json'
    started=time.monotonic();previous=ticks();samples=[]
    while time.monotonic()-started<args.seconds:
        memory=Memory();memory.length=ctypes.sizeof(memory)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):raise OSError('Memory query failed')
        current=ticks();total=(current[1]-previous[1])+(current[2]-previous[2]);idle=current[0]-previous[0];previous=current
        row={'elapsed_seconds':time.monotonic()-started,'host_ram_total_bytes':memory.total,'host_ram_used_bytes':memory.total-memory.available,'host_cpu_percent':100*(total-idle)/total if total else None}
        try:
            output=subprocess.check_output(['docker','stats','--no-stream','--format','{{json .}}'],text=True,timeout=15)
            row['containers']=[json.loads(line) for line in output.splitlines() if line.strip()]
            gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip().split(',')
            row['gpu_memory_mib']=int(gpu[0]);row['gpu_utilization_percent']=int(gpu[1])
        except Exception as e:row['telemetry_error']=str(e)
        samples.append(row)
        dest.write_text(json.dumps({'limits':'Observed shared-laptop samples; GPU includes desktop/other processes. Sampling started after scale setup began, so these are observed peaks, not guaranteed absolute peaks.','samples':samples},indent=2),encoding='utf-8')
        time.sleep(2)
    assert samples
    print(json.dumps({'samples':len(samples),'peak_observed_cpu_percent':max(s['host_cpu_percent'] or 0 for s in samples),'peak_observed_ram_bytes':max(s['host_ram_used_bytes'] for s in samples),'peak_observed_gpu_mib':max((s.get('gpu_memory_mib',0) for s in samples))}))

if __name__=='__main__':main()
