import time, urllib.request, re

def fps(url, label, dur=8):
    t0 = time.time()
    r = urllib.request.urlopen(url, timeout=dur + 3)
    start = time.time()
    n = 0
    while time.time() - start < dur:
        chunk = r.read(65536)
        if chunk:
            n += chunk.count(b'\xff\xd8\xff')
    elapsed = time.time() - start
    r.close()
    # 持续流帧到达率: 反映画面推进是否稳定(无堆积/卡顿)
    print(f"{label}: ~{n} frames in {elapsed:.1f}s => {n/elapsed:.1f} fps (到达率)")

fps("http://192.168.0.2:8082/camera", "彩色(设备)")
fps("http://192.168.0.2:8082/depth", "深度(设备)")
fps("http://192.168.0.2:8082/ir", "红外(设备)")