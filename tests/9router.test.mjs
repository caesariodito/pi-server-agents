import assert from 'node:assert/strict';
import { test } from 'node:test';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import provider, { loadNinerouterEnv, validateModels } from '../extensions/9router-models.ts';

test('credentials resolve per variable without login shell or secret output',()=>{
  const home=mkdtempSync(join(tmpdir(),'pi-router-test-'));
  const before={...process.env};
  try{
    process.env.HOME=home;delete process.env.NINEROUTER_URL;delete process.env.NINEROUTER_KEY;
    mkdirSync(join(home,'.config/9router'),{recursive:true});
    writeFileSync(join(home,'.config/9router/env'),"export NINEROUTER_URL='https://router.example'\nexport NINEROUTER_KEY='dummy-file-key'\n",{mode:0o600});
    process.env.NINEROUTER_URL='https://override.example';
    assert.deepEqual(loadNinerouterEnv(),{url:'https://override.example',key:'dummy-file-key'});
    delete process.env.NINEROUTER_URL;process.env.NINEROUTER_KEY='dummy-override';
    assert.deepEqual(loadNinerouterEnv(),{url:'https://router.example',key:'dummy-override'});
    for(const url of ['file:///tmp/no','https://user:secret@router.example','https://router.example?key=secret']){
      process.env.NINEROUTER_URL=url;assert.throws(loadNinerouterEnv,/Invalid 9Router URL/);
    }
  }finally{for(const k of Object.keys(process.env))if(!(k in before))delete process.env[k];Object.assign(process.env,before);rmSync(home,{recursive:true,force:true});}
});
test('model payload validation rejects invalid IDs and token limits',()=>{
  for(const payload of [{}, {data:[]},{data:[{id:''}]},{data:[{id:'a'},{id:'a'}]},{data:[{id:'a',context_length:-1}]}])assert.throws(()=>validateModels(payload));
  assert.equal(validateModels({data:[{id:'ok',capabilities:{vision:true,reasoning:true}}]})[0].reasoning,true);
});
test('discovery failure keeps safe fallback and does not leak gateway error',async()=>{
  const before={...process.env}, originalFetch=globalThis.fetch, warn=console.warn, messages=[], registrations=[];
  const home=mkdtempSync(join(tmpdir(),'pi-router-fallback-'));
  try{
    process.env.HOME=home;process.env.PI_CODING_AGENT_DIR=home;
    writeFileSync(join(home,'settings.json'),JSON.stringify({defaultProvider:'9router',defaultModel:'my-default'}));
    process.env.NINEROUTER_URL='https://router.example';process.env.NINEROUTER_KEY='dummy-secret';
    globalThis.fetch=async()=>{throw Error('private dummy-secret')};console.warn=s=>messages.push(s);
    await provider({registerProvider:(...args)=>registrations.push(args)});
    assert.equal(registrations.length,1);assert.equal(registrations[0][1].models[0].id,'my-default');
    assert.ok(!messages.join('').includes('dummy-secret'));
    globalThis.fetch=async(_url,options)=>{assert.equal(options.redirect,'error');return {ok:true,json:async()=>({data:[{id:'remote'}]})}};
    await provider({registerProvider:(...args)=>registrations.push(args)});
    assert.equal(registrations.at(-1)[1].models[0].id,'remote');
  }finally{rmSync(home,{recursive:true,force:true});globalThis.fetch=originalFetch;console.warn=warn;for(const k of Object.keys(process.env))if(!(k in before))delete process.env[k];Object.assign(process.env,before);}
});
