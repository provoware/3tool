# =========================================
# QUICKSTART
# CLI-Encode:  python3 videobatch_extra.py --img 1.jpg 2.jpg --aud 1.mp3 2.mp3 --out outdir
# Selftests:   python3 videobatch_extra.py --selftest
# Edit:        micro videobatch_extra.py
# =========================================

# videobatch_extra.py
from __future__ import annotations
import sys, subprocess, re, tempfile
from pathlib import Path
from datetime import datetime
from typing import List

def human_time(s:int)->str:
    s=int(s); m,s=divmod(s,60); h,m=divmod(m,60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

def build_out_name(audio:str, out_dir:Path)->Path:
    return out_dir / f"{Path(audio).stem}_{datetime.now().strftime('%Y%m%d-%H%M%S')}.mp4"

def cli_encode(images:List[str], audios:List[str], out_dir:str,
               width=1920,height=1080,crf=23,preset="ultrafast",abitrate="192k")->int:
    out_dir_p=Path(out_dir); out_dir_p.mkdir(parents=True, exist_ok=True)
    if len(images)!=len(audios):
        print("Fehler: Anzahl Bilder != Anzahl Audios"); return 1
    total=len(images); done=0
    for i,(img,aud) in enumerate(zip(images,audios),1):
        if not Path(img).exists() or not Path(aud).exists():
            print(f"[{i}/{total}] FEHLT: {img} / {aud}"); continue
        out_file=build_out_name(aud,out_dir_p)
        cmd=["ffmpeg","-y","-loop","1","-i",img,
             "-i",aud,
             "-c:v","libx264","-tune","stillimage",
             "-vf",f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
             "-c:a","aac","-b:a",abitrate,
             "-shortest","-preset",preset,"-crf",str(crf),
             str(out_file)]
        res=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        if res.returncode==0: done+=1
        else: print("FFmpeg-Fehler:", res.stderr.splitlines()[-1] if res.stderr else "unbekannt")
    print(f"Fertig: {done}/{total}")
    return 0

def run_selftests()->int:
    assert human_time(65)=="01:05"
    with tempfile.TemporaryDirectory() as td:
        out=build_out_name(str(Path(td)/"a.mp3"), Path(td))
        assert out.name.endswith(".mp4")
        assert re.search(r"a_\d{8}-\d{6}\.mp4$", out.name)
    print("Selftests OK")
    return 0

def main():
    import argparse
    p=argparse.ArgumentParser(description="VideoBatchTool CLI / Tests")
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--img",nargs="+")
    p.add_argument("--aud",nargs="+")
    p.add_argument("--out",default=".")
    p.add_argument("--width",type=int,default=1920)
    p.add_argument("--height",type=int,default=1080)
    p.add_argument("--crf",type=int,default=23)
    p.add_argument("--preset",default="ultrafast")
    p.add_argument("--abitrate",default="192k")
    args=p.parse_args()

    if args.selftest: sys.exit(run_selftests())
    if args.img and args.aud:
        sys.exit(cli_encode(args.img,args.aud,args.out,args.width,args.height,args.crf,args.preset,args.abitrate))
    print("GUI starten: python3 videobatch_launcher.py")

if __name__=="__main__":
    main()
