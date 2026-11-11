import {describe,it,expect} from 'vitest';
import {postRequest} from './direct';
describe('public post links',()=>{
 it('accepts shared X and legacy Twitter links',()=>{
  expect(postRequest('https://x.com/NASA/status/1390245710652551170?s=20').id).toBe('1390245710652551170');
  expect(postRequest('https://twitter.com/i/web/status/1390245710652551170').token).toBe(postRequest('https://x.com/NASA/status/1390245710652551170').token);
 });
 it.each(['http://x.com/a/status/1','https://x.com.evil.test/a/status/1','https://user@x.com/a/status/1','https://x.com:8443/a/status/1','https://x.com/a','https://x.com/a/status/1/extra','https://127.0.0.1/a/status/1'])('rejects %s',url=>expect(()=>postRequest(url)).toThrow());
});
