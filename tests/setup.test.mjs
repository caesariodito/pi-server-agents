import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync, readdirSync, rmSync, cpSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { test } from 'node:test';
const source = resolve(import.meta.dirname, '..');
const shared = JSON.parse(readFileSync(join(source,'profiles/shared-skills.json'),'utf8'));
test('shared skill dependency uses exact reviewed commit and explicit profiles',()=>{
  assert.match(shared.source,/^git:github\.com\/caesariodito\/skills@[a-f0-9]{40}$/);
  assert.ok(shared.base.includes('server-operations'));
  assert.ok(shared.daily.includes('engineering-lifecycle'));
  for (const name of shared.daily) assert.ok(!existsSync(join(source,'profiles/daily/skills',name,'SKILL.md')));
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
    assert.equal(settings.theme,'custom');assert.equal(settings.packages.length,3);
    assert.deepEqual(settings.packages.at(-1).skills,shared.base.map(name=>`${name}/SKILL.md`));
    assert.ok(!existsSync(join(agent,'daily-skills')));
    assert.ok(!readFileSync(join(agent,'AGENTS.md'),'utf8').includes('git push'));
    assert.ok(readdirSync(agent).some(p=>p.startsWith('AGENTS.md.backup.')));
    result=configure(home,'1');assert.equal(result.status,0,result.stderr);
    settings=JSON.parse(readFileSync(join(agent,'settings.json')));
    assert.ok(settings.packages.includes('npm:pi-web-access@0.45.0'));
    assert.ok(settings.packages.includes('npm:mine@1.0.0'));
    assert.ok(!existsSync(join(agent,'daily-skills')));
    assert.deepEqual(settings.packages.at(-1).skills,[...shared.base,...shared.daily].map(name=>`${name}/SKILL.md`));
    const before=readFileSync(join(agent,'settings.json'),'utf8');
    result=configure(home,'0');assert.equal(result.status,0,result.stderr);
    assert.equal(readFileSync(join(agent,'settings.json'),'utf8'),before);
    assert.equal(readFileSync(join(agent,'auth.json'),'utf8'),'private-auth');
    assert.equal(readFileSync(join(agent,'unknown'),'utf8'),'keep');
    assert.ok(existsSync(join(agent,'.git')));
    assert.deepEqual(JSON.parse(readFileSync(join(agent,'models.json'))),{providers:{}});
  }finally{rmSync(home,{recursive:true,force:true});}
});
test('empty migration repair is backed up and idempotent; custom providers stay unchanged',()=>{
  for(const initial of [{}, {providers:{}}, {providers:{custom:{baseUrl:'https://example.com/v1'}}}]){
    const home=temp(), agent=join(home,'agent');
    try{
      mkdirSync(agent);
      const original=JSON.stringify(initial);
      writeFileSync(join(agent,'models.json'),original);
      let result=configure(home);assert.equal(result.status,0,result.stderr);
      const expected=Object.keys(initial).length===0 ? {providers:{}} : initial;
      assert.deepEqual(JSON.parse(readFileSync(join(agent,'models.json'))),expected);
      const backups=()=>readdirSync(agent).filter(p=>p.startsWith('models.json.backup.'));
      const before=backups();
      assert.equal(before.length,Object.keys(initial).length===0 ? 1 : 0);
      if(before.length)assert.equal(readFileSync(join(agent,before[0]),'utf8'),original);
      else assert.equal(readFileSync(join(agent,'models.json'),'utf8'),original);
      result=configure(home);assert.equal(result.status,0,result.stderr);
      assert.deepEqual(backups(),before);
      assert.deepEqual(JSON.parse(readFileSync(join(agent,'models.json'))),expected);
    }finally{rmSync(home,{recursive:true,force:true});}
  }
});
test('legacy snapshot discovery migrates without deleting files or duplicating shared package',()=>{
  const home=temp(),agent=join(home,'agent');
  try{
    mkdirSync(join(agent,'daily-skills/custom'),{recursive:true});
    writeFileSync(join(agent,'daily-skills/custom/SKILL.md'),'keep-local');
    writeFileSync(join(agent,'.daily-workflow'),'enabled\n');
    writeFileSync(join(agent,'settings.json'),JSON.stringify({skills:[join(agent,'daily-skills'),'~/.pi/agent/daily-skills','/custom/skills'],packages:[{source:'https://github.com/caesariodito/skills@old',skills:['*']},'npm:mine@1.0.0']}));
    for(let i=0;i<2;i++){
      const r=configure(home);assert.equal(r.status,0,r.stderr);
      const settings=JSON.parse(readFileSync(join(agent,'settings.json'),'utf8'));
      assert.deepEqual(settings.skills,['/custom/skills']);
      assert.equal(settings.packages.filter(p=>typeof p==='object'&&p.source.includes('caesariodito/skills')).length,1);
      assert.equal(readFileSync(join(agent,'daily-skills/custom/SKILL.md'),'utf8'),'keep-local');
    }
  }finally{rmSync(home,{recursive:true,force:true});}
});
test('exact former gateway moves outside discovery with contents preserved',()=>{
  const home=temp(),agent=join(home,'agent');
  try{
    const original=spawnSync('git',['-C',source,'show','833318e9edbb0fe4bee5f208e3b0dce2d35e9296:skills/9router/SKILL.md'],{encoding:'utf8'});
    assert.equal(original.status,0,original.stderr);
    mkdirSync(join(agent,'skills/9router'),{recursive:true});
    writeFileSync(join(agent,'skills/9router/SKILL.md'),original.stdout);
    const r=configure(home);assert.equal(r.status,0,r.stderr);
    assert.ok(!existsSync(join(agent,'skills/9router')));
    const backup=readdirSync(join(agent,'retired-skills'))[0];
    assert.equal(readFileSync(join(agent,'retired-skills',backup,'SKILL.md'),'utf8'),original.stdout);
  }finally{rmSync(home,{recursive:true,force:true});}
});
test('modified legacy gateway blocks before runtime writes',()=>{
  const home=temp(),agent=join(home,'agent');
  try{
    mkdirSync(join(agent,'skills/9router'),{recursive:true});
    writeFileSync(join(agent,'skills/9router/SKILL.md'),'custom');
    const r=configure(home);assert.notEqual(r.status,0);assert.match(r.stderr,/differs from former managed source/);
    assert.ok(!existsSync(join(agent,'settings.json')));
    assert.equal(readFileSync(join(agent,'skills/9router/SKILL.md'),'utf8'),'custom');
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
function coreFixture(home){
  const bin=join(home,'bin');mkdirSync(bin);
  writeFileSync(join(bin,'herdr-core'),'#!/bin/bash\nprintf "%s\\n" "$*" >> "$HOME/core-calls"\necho "hc 0.1.19"\n',{mode:0o700});
  return {HOME:home,PATH:`${bin}:${process.env.PATH}`};
}
test('retired Ovis entrypoint fails without calling legacy tools',()=>{
  const home=temp();try{
    const r=run('bash',[join(source,'scripts/install-ovis.sh')],{HOME:home});
    assert.notEqual(r.status,0);assert.match(r.stderr,/retired/);
  }finally{rmSync(home,{recursive:true,force:true});}
});
test('full installer combinations preserve runtime and refuse dirty source',()=>{
  for(const daily of ['0','1']){
    const home=temp();try{
      const env=coreFixture(home);
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
      const config={...env,PI_SETUP_MODE:'missing',PI_SETUP_DAILY_WORKFLOW:daily,PI_SETUP_OVIS:'0',PI_SETUP_QMD:'0',NINEROUTER_URL:'https://gateway.example',NINEROUTER_KEY:'dummy'};
      for(let i=0;i<2;i++){
        const r=run('bash',[runner],config);assert.equal(r.status,0,r.stderr);
      }
      const agent=join(home,'.pi/agent');assert.ok(!existsSync(join(agent,'daily-skills')));
      const settings=JSON.parse(readFileSync(join(agent,'settings.json'),'utf8'));
      assert.equal(settings.packages.at(-1).source,shared.source);
      assert.ok(!readFileSync(join(agent,'AGENTS.md'),'utf8').includes('git push'));
      const r=run('bash',[runner],{...config,DIRTY:'1'});assert.notEqual(r.status,0);assert.match(r.stderr,/local changes/);
    }finally{rmSync(home,{recursive:true,force:true});}
  }
});

test('Ovis opt-in fails before any installer action',()=>{
  const r=run('bash',[join(source,'install.sh')],{PI_SETUP_OVIS:'1',HOME:'/nonexistent'});
  assert.notEqual(r.status,0);assert.match(r.stderr,/retired/);assert.ok(!r.stdout.includes('Installing'));
});
test('missing core installer receives pinned version and user-local destination',()=>{
  const home=temp();try{
    const bin=join(home,'bin');mkdirSync(bin);
    const installer=join(home,'fake-installer.sh');
    writeFileSync(installer,'#!/bin/sh\nset -eu\n[ "$HC_VERSION" = 0.1.19 ]\n[ "$HC_INSTALL_DIR" = "$HOME/.local/bin" ]\nmkdir -p "$HC_INSTALL_DIR"\nprintf "#!/bin/sh\\necho hc 0.1.19\\n" > "$HC_INSTALL_DIR/herdr-core"\nchmod 700 "$HC_INSTALL_DIR/herdr-core"\n');
    writeFileSync(join(bin,'curl'),'#!/bin/sh\n[ "${FAIL_DOWNLOAD:-0}" = 0 ] || exit 7\ncp "$HOME/fake-installer.sh" "$4"\n',{mode:0o700});
    const script=readFileSync(join(source,'install.sh'),'utf8');
    const start=script.indexOf('export PATH="$HOME/.local/bin:$PATH"');
    const end=script.indexOf("grep -Fq 'export PATH=",start);
    const block=script.slice(start,end);
    const prelude='set -eu\nCORE_VERSION=0.1.19\nHERDR_INSTALLER_URL=https://releases.herdr.dev/core/install.sh\nlog() { :; }\ndie() { echo "$*" >&2; exit 1; }\ncommand() { if [ "$1" = -v ] && [ "$2" = herdr-core ]; then [ -x "$HOME/.local/bin/herdr-core" ]; else builtin command "$@"; fi; }\n';
    let r=run('bash',['-c',prelude+block],{HOME:home,PATH:`${bin}:${process.env.PATH}`,FAIL_DOWNLOAD:'1'});
    assert.notEqual(r.status,0);assert.ok(!existsSync(join(home,'.local/bin/herdr-core')));
    r=run('bash',['-c',prelude+block],{HOME:home,PATH:`${bin}:${process.env.PATH}`});
    assert.equal(r.status,0,r.stderr);assert.ok(existsSync(join(home,'.local/bin/herdr-core')));
  }finally{rmSync(home,{recursive:true,force:true});}
});
test('core integration has no legacy install, plugin or startup commands',()=>{
  const script=readFileSync(join(source,'install.sh'),'utf8');
  assert.ok(script.includes('https://releases.herdr.dev/core/install.sh'));
  assert.ok(script.includes('HC_VERSION="$CORE_VERSION"'));
  assert.ok(!/command -v herdr |herdr plugin|herdr server|herdr.dev\/install.sh/.test(script));
});
