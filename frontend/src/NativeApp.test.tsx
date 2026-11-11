import {render,screen,fireEvent,waitFor,cleanup} from '@testing-library/react';
import {afterEach,beforeEach,expect,it,vi} from 'vitest';
const native=vi.hoisted(()=>({analyze:vi.fn(),download:vi.fn(),status:vi.fn(),cancel:vi.fn()}));
vi.mock('./services/direct',async()=>({...await vi.importActual('./services/direct'),DirectVideo:native}));
import NativeApp from './NativeApp';
afterEach(cleanup);
beforeEach(()=>{vi.resetAllMocks();localStorage.clear();});
it('extracts, chooses a format and saves directly without fetching a backend',async()=>{
 const fetch=vi.spyOn(globalThis,'fetch');
 native.analyze.mockResolvedValue({title:'Public video',qualities:[{id:'low',label:'640 × 360'},{id:'high',label:'1280 × 720'}]});
 native.download.mockResolvedValue({id:'42'});native.status.mockResolvedValue({status:8,bytes:1000,total:1000});
 render(<NativeApp/>);
 fireEvent.change(screen.getByLabelText('X or Twitter post URL'),{target:{value:'https://x.com/NASA/status/1390245710652551170'}});
 fireEvent.click(screen.getByText('Find my video'));
 await screen.findByText('Public video');
 fireEvent.change(screen.getByLabelText('Choose quality'),{target:{value:'high'}});
 fireEvent.click(screen.getByText('Download to Android'));
 await screen.findByText('Saved to Android Downloads');
 expect(native.download).toHaveBeenCalledWith({format:'high'});expect(fetch).not.toHaveBeenCalled();fetch.mockRestore();
});
it('shows extraction errors and permits retry',async()=>{
 native.analyze.mockRejectedValue(new Error('Post unavailable'));
 render(<NativeApp/>);fireEvent.change(screen.getByLabelText('X or Twitter post URL'),{target:{value:'https://x.com/a/status/123'}});fireEvent.click(screen.getByText('Find my video'));
 expect(await screen.findByRole('alert')).toHaveTextContent('Post unavailable');
 await waitFor(()=>expect(screen.getByText('Find my video')).not.toBeDisabled());
});
it('cancels an Android download',async()=>{
 native.analyze.mockResolvedValue({title:'Video',qualities:[{id:'one',label:'MP4'}]});native.download.mockResolvedValue({id:'9'});native.status.mockResolvedValue({status:2,bytes:50,total:100});native.cancel.mockResolvedValue(undefined);
 render(<NativeApp/>);fireEvent.change(screen.getByLabelText('X or Twitter post URL'),{target:{value:'https://x.com/a/status/123'}});fireEvent.click(screen.getByText('Find my video'));await screen.findByText('Video');fireEvent.click(screen.getByText('Download to Android'));fireEvent.click(await screen.findByText('Cancel download'));await screen.findByText('Download cancelled.');expect(native.cancel).toHaveBeenCalledWith({id:'9'});
});
