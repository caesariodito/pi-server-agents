#!/usr/bin/env python3
from __future__ import annotations
import copy,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;BUILD=ROOT/'scripts/build.py';EXAMPLE=ROOT/'reference/example.json'
def run(src,out):return subprocess.run(['python3',str(BUILD),str(src),str(out)],capture_output=True,text=True)
def reject(base,mutate,expected,d):
 s=copy.deepcopy(base);mutate(s);src=d/'bad.json';src.write_text(json.dumps(s));r=run(src,d/'bad.html');assert r.returncode!=0;assert expected in r.stderr,r.stderr
def main():
 base=json.loads(EXAMPLE.read_text())
 with tempfile.TemporaryDirectory() as raw:
  d=Path(raw);out=d/'spec.html';r=run(EXAMPLE,out);assert r.returncode==0,r.stderr;page=out.read_text()
  assert page.startswith('<!doctype html>');assert '<link' not in page and '<script src=' not in page and 'https://' not in page
  assert page.count('class="sec" id=')==13
  assert page.index('<span class="num">1</span>Overview')<page.index('<span class="num">13</span>Change log')
  assert page.count('data-diagram="')==3
  assert 'data-answer="TD-01"' in page and 'data-answer="TQ1"' in page
  ids=[x['id'] for k in ('flows','contracts','processing_rules','examples','decisions','open_questions') for x in base[k]]+[x['id'] for x in base['architecture']['components']]
  for i in ids:assert page.count(f'id="{i}"')==1,f'missing or duplicate anchor {i}'
  assert {i.rstrip('0123456789').rstrip('-') for i in ids}=={'TS','C','CT','PR','EX','TD','TQ'}
  assert 'class="layout"' in page and 'class="sidebar"' in page and 'class="toolbar"' in page
  assert 'id="progress-bar"' in page and 'id="review"' in page
  masthead=page.split('<header class="masthead">',1)[1].split('</header>',1)[0]
  assert './implementation-plan.html' not in masthead
  assert './implementation-plan.html' in page.split('<div class="main">',1)[0]
  detailed=copy.deepcopy(base);detailed['links'].update({'diagram reference':'./diagrams.md','flow diagrams':'./diagrams.md#sequence','architecture diagrams':'./diagrams.md#deployment','data diagrams':'./diagrams.md#erd'})
  source=d/'detailed.json';source.write_text(json.dumps(detailed));result=run(source,d/'detailed.html');assert result.returncode==0,result.stderr
  detail=(d/'detailed.html').read_text();assert 'href="./diagrams.md"' in detail.split('<div class="main">',1)[0];assert detail.count('Detailed diagram reference')==3
  reject(base,lambda s:s.update(status='review'),'invalid status',d)
  reject(base,lambda s:s['flows'][1]['messages'][0].update(to='Unknown'),'endpoint is not a participant',d)
  reject(base,lambda s:s['examples'][0]['rows'][0].pop(),'wrong cell count',d)
  reject(base,lambda s:s['data_model']['relationships'][0].update(to='missing'),'unknown entity',d)
  reject(base,lambda s:s['decisions'][0]['options'][0].update(recommended=False),'exactly one recommended',d)
  reject(base,lambda s:s['architecture']['components'][0].update(id='COMP-1'),'component 1: invalid ID',d)
 print('technical-spec smoke test: PASS')
if __name__=='__main__':main()
