import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync, readdirSync, rmSync, cpSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { test } from 'node:test';
const source = resolve(import.meta.dirname, '..');
test('curated skill entrypoints and local skill links are portable',()=>{
  const root=join(source,'profiles/daily/skills');
  for(const entry of readdirSync(root)){
    const path=join(root,entry,'SKILL.md'), text=readFileSync(path,'utf8');
    assert.match(text,/^name: [a-z0-9-]+$/m);assert.match(text,/^description:/m);
    assert.ok(!/\/Users\/wolter|~\/\.dotfiles/.test(text));
    for(const match of text.matchAll(/\]\(([^)]+)\)/g)){
      const target=match[1].split('#')[0];
      if(target&&!target.includes('://')&&!target.startsWith('/'))assert.ok(existsSync(resolve(root,entry,target)),`${entry}: ${target}`);
    }
  }
});
const temp = () => mkdtempSync(join(tmpdir(), 'pi-setup-test-'));
function run(command, args, env={}) {
  return spawnSync(command,args,{encoding:'utf8',timeout:15000,env:{PATH:process.env.PATH,...env}});
}
function configure(home,daily='0') {
  return run(process.execPath,[join(source,'scripts/configure-runtime.mjs'),source,join(home,'agent'),daily],{HOME:home});
}
test('runtime profile opt-in, reruns and legacy migration preserve private/user files',()=>{
  const home=temp(), agent=join(home,'agent');
  try{
    mkdirSync(join(agent,'.git'),{recursive:true});
    writeFileSync(join(agent,'auth.json'),'private-auth');
    writeFileSync(join(agent,'unknown'),'keep');
    writeFileSync(join(agent,'AGENTS.md'),'old repository maintenance');
    writeFileSync(join(agent,'models.json'),JSON.stringify({providers:{'9router':{baseUrl:'http://100.70.192.32:20128/v1',apiKey:'legacy-command'}}}));
    writeFileSync(join(agent,'settings.json'),JSON.stringify({theme:'custom',packages:['npm:pi-memory@0.4.2','npm:mine@1.0.0'],skills:[]}));
    let result=configure(home);assert.equal(result.status,0,result.stderr);
    let settings=JSON.parse(readFileSync(join(agent,'settings.json')));
    assert.equal(settings.theme,'custom');assert.equal(settings.packages.length,2);
    assert.ok(!existsSync(join(agent,'daily-skills')));
    assert.ok(!readFileSync(join(agent,'AGENTS.md'),'utf8').includes('git push'));
    assert.ok(readdirSync(agent).some(p=>p.startsWith('AGENTS.md.backup.')));
    result=configure(home,'1');assert.equal(result.status,0,result.stderr);
    settings=JSON.parse(readFileSync(join(agent,'settings.json')));
    assert.ok(settings.packages.includes('npm:pi-web-access@0.45.0'));
    assert.ok(settings.packages.includes('npm:mine@1.0.0'));
    assert.ok(existsSync(join(agent,'daily-skills/security-audit/SKILL.md')));
    assert.ok(readFileSync(join(agent,'daily-skills/engineering-lifecycle/SKILL.md'),'utf8').includes(join(agent,'daily-skills/project-init/references/')));
    const before=readFileSync(join(agent,'settings.json'),'utf8');
    result=configure(home,'0');assert.equal(result.status,0,result.stderr);
    assert.equal(readFileSync(join(agent,'settings.json'),'utf8'),before);
    assert.equal(readFileSync(join(agent,'auth.json'),'utf8'),'private-auth');
    assert.equal(readFileSync(join(agent,'unknown'),'utf8'),'keep');
    assert.ok(existsSync(join(agent,'.git')));
    assert.deepEqual(JSON.parse(readFileSync(join(agent,'models.json'))),{});
  }finally{rmSync(home,{recursive:true,force:true});}
});
test('invalid settings stop before managed runtime writes',()=>{
  const home=temp(), agent=join(home,'agent');
  try{
    mkdirSync(agent);writeFileSync(join(agent,'settings.json'),'{bad');
    const r=configure(home,'1');assert.notEqual(r.status,0);assert.ok(!existsSync(join(agent,'AGENTS.md')));
  }finally{rmSync(home,{recursive:true,force:true});}
});
test('invalid flags fail before tool installers and root prompts',()=>{
  for(const flag of ['PI_SETUP_DAILY_WORKFLOW','PI_SETUP_OVIS','PI_SETUP_QMD','PI_SETUP_MODE']){
    const r=run('bash',[join(source,'install.sh')],{[flag]:'invalid',HOME:'/nonexistent'});
    assert.notEqual(r.status,0);assert.match(r.stderr,new RegExp(flag));assert.ok(!r.stdout.includes('Installing'));
  }
});
function ovisFixture(home,{version='herdr 0.9.4',bun='1.4.0',plugins='{"result":{"plugins":[]}}',running=false}={}){
  const bin=join(home,'bin');mkdirSync(bin);
  writeFileSync(join(bin,'herdr'),`#!/bin/bash\nprintf '%s\\n' "$*" >> "$HOME/calls"\ncase "$*" in\n'--version') echo '${version}' ;;\n'plugin config-dir devswha.ovis') echo "$HOME/ovis-config" ;;\n'plugin list --json') echo '${plugins}' ;;\n'status server') exit ${running?0:1} ;;\nesac\n`,{mode:0o700});
  writeFileSync(join(bin,'bun'),`#!/bin/bash\necho '${bun}'\n`,{mode:0o700});
  writeFileSync(join(bin,'curl'),'#!/bin/bash\necho \'{"ok":true,"herdr":{"version":"0.9.4"}}\'\n',{mode:0o700});
  return {HOME:home,PATH:`${bin}:${process.env.PATH}`};
}
test('Ovis installs pinned plugin independently; no network exposure or Herdr restart',()=>{
  for(const running of [false,true]){
    const home=temp();try{
      const env=ovisFixture(home,{running});const r=run('bash',[join(source,'scripts/install-ovis.sh'),'v0.4.21'],env);
      assert.equal(r.status,0,r.stderr);const calls=readFileSync(join(home,'calls'),'utf8');
      assert.match(calls,/plugin install --ref v0.4.21 --yes devswha\/ovis/);
      assert.ok(!/server stop|tailscale|phone|relay/.test(calls));
      assert.match(readFileSync(join(home,'ovis-config/env'),'utf8'),/HOST=127.0.0.1/);
      assert.match(r.stdout,running ? /Ovis healthy/ : /Startup pending/);
    }finally{rmSync(home,{recursive:true,force:true});}
  }
});
test('full installer combinations preserve runtime and refuse dirty source',()=>{
  for(const daily of ['0','1'])for(const ovis of ['0','1']){
    const home=temp();try{
      const env=ovisFixture(home);
      const bin=join(home,'bin'),checkout=join(home,'.local/share/pi-server-agents');
      cpSync(source,checkout,{recursive:true,filter:path=>!path.includes('/.git')&&!path.includes('/.scratch')&&!path.includes('/__pycache__')});
      mkdirSync(join(checkout,'.git'));
      const script=readFileSync(join(source,'install.sh'),'utf8').replace('\nconfirm_root_install\n','\n# Root confirmation separately covered; fixture never installs real tools.\n');
      const runner=join(home,'installer.sh');writeFileSync(runner,script);
      const tool=(name,body)=>writeFileSync(join(bin,name),'#!/bin/bash\n'+body+'\n',{mode:0o700});
      tool('git','case "$*" in *"remote get-url origin"*) echo https://github.com/caesariodito/pi-server-agents ;; *"status --porcelain"*) [[ "${DIRTY:-0}" == 0 ]] || echo " M settings.json" ;; esac; exit 0');
      tool('pi','if [[ "$1" == --version ]]; then echo 1.4.0; fi');
      tool('npm','echo "Unexpected npm install" >&2; exit 99');
      tool('tmux','[[ "$1" != list-sessions ]]');
      tool('infocmp','exit 1');
      mkdirSync(join(home,'.nvm'));writeFileSync(join(home,'.nvm/nvm.sh'),'nvm() { [[ "$1" != version ]] || echo v24.0.0; return 0; }\n');
      const config={...env,PI_SETUP_MODE:'missing',PI_SETUP_DAILY_WORKFLOW:daily,PI_SETUP_OVIS:ovis,PI_SETUP_QMD:'0',NINEROUTER_URL:'https://gateway.example',NINEROUTER_KEY:'dummy'};
      for(let i=0;i<2;i++){
        const r=run('bash',[runner],config);assert.equal(r.status,0,r.stderr);
      }
      const agent=join(home,'.pi/agent');assert.equal(existsSync(join(agent,'daily-skills')),daily==='1');
      assert.ok(!readFileSync(join(agent,'AGENTS.md'),'utf8').includes('git push'));
      const r=run('bash',[runner],{...config,DIRTY:'1'});assert.notEqual(r.status,0);assert.match(r.stderr,/local changes/);
    }finally{rmSync(home,{recursive:true,force:true});}
  }
});

test('Ovis refuses old tools, malformed plugin state, and existing public bind',()=>{
  for(const options of [{version:'herdr 0.8.0'},{bun:'1.3.0'},{plugins:'{}'},{public:true}]){
    const home=temp();try{
      const env=ovisFixture(home,options);
      if(options.public){mkdirSync(join(home,'ovis-config'));writeFileSync(join(home,'ovis-config/env'),'HOST=0.0.0.0\n');}
      const r=run('bash',[join(source,'scripts/install-ovis.sh'),'v0.4.21'],env);
      assert.notEqual(r.status,0);assert.ok(!readFileSync(join(home,'calls'),'utf8').includes('plugin install'));
    }finally{rmSync(home,{recursive:true,force:true});}
  }
});
