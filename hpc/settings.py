#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from common import ROOT,load_yaml,config,path
if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1]=='--help':
  print('Usage: settings.py SETTING_KEY; read HPC resource/config setting');raise SystemExit(0 if '--help' in sys.argv else 1)
 c=load_yaml(ROOT/'config/hpc_resources.yaml')
 print(c.get(sys.argv[1], config().get(sys.argv[1],'')))
