const assert=require('node:assert/strict'),ts=require('typescript'),fs=require('node:fs');
require.extensions['.ts']=(module,file)=>module._compile(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,file);
const {visitorTime}=require('../lib/visitor-time.ts');
const winter=Date.parse('2026-01-15T12:00:00Z'),summer=Date.parse('2026-07-15T12:00:00Z');
for(const [zone,prefix] of [['UTC','12:00:00'],['Asia/Yerevan','16:00:00'],['Asia/Tehran','15:30:00'],['Asia/Kathmandu','17:45:00'],['America/New_York','07:00:00']]){
 const result=visitorTime(winter,zone);assert.ok(result.time.startsWith(prefix));assert.equal(result.timeZone,zone);assert.ok(result.label.includes(zone));
}
assert.ok(visitorTime(summer,'America/New_York').time.startsWith('08:00:00'));
assert.equal(visitorTime(winter).timeZone,Intl.DateTimeFormat().resolvedOptions().timeZone);
console.log('PASS: visitor timezone, UTC and fractional offsets, daylight-saving transitions');
