const {chromium}=require('playwright');const {spawn}=require('child_process');
(async()=>{
const b=await chromium.launch({args:['--allow-file-access-from-files']});
const p=await b.newPage({viewport:{width:1080,height:1920}});
p.on('pageerror',e=>console.log('ERR',e.message));
await p.goto('file://'+process.cwd()+'/anim.html');await p.evaluate(()=>window.ready);
const ff=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate','30','-c:v','mjpeg','-i','-','-i','music.wav',
 '-c:v','libx264','-preset','slow','-crf','17','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart','out.mp4'],{stdio:['pipe','inherit','inherit']});
for(let f=0;f<900;f++){
  const d=await p.evaluate(t=>{render(t);return document.getElementById('c').toDataURL('image/jpeg',0.95)},f/30);
  const buf=Buffer.from(d.split(',')[1],'base64');
  if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));
}
ff.stdin.end();await new Promise(r=>ff.on('close',r));await b.close();console.log('done');})();
