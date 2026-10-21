<!DOCTYPE html>
<html lang="ky"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Алтын Сөз</title>
<style>
:root{--cd:#fff8e6;--tx:#2e1c0e;--mu:#7a5a3a;--ac:#f2b705;--rd:#c8102e;--tq:#0a9e9a;--b1:#4db8ff;--b2:#fff0b8;--b3:#79c95f;--ln:#e9c46a;--orn:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='34' height='18'%3E%3Cpath d='M2 16C2 6 10 2 16 6C20 9 16 15 12 12C9 10 11 7 13 9' fill='none' stroke='%23ffd23c' stroke-width='2'/%3E%3Cpath d='M32 16C32 6 24 2 18 6' fill='none' stroke='%23fff' stroke-width='2'/%3E%3C/svg%3E");box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
@media(prefers-color-scheme:dark){:root:not([data-theme="light"]){--cd:#33261b;--tx:#fff0d2;--mu:#d2b88f;--b1:#1b3a66;--b2:#4a3a5e;--b3:#25503a;--ln:#8a6a2a}}
:root[data-theme="dark"]{--cd:#33261b;--tx:#fff0d2;--mu:#d2b88f;--b1:#1b3a66;--b2:#4a3a5e;--b3:#25503a;--ln:#8a6a2a}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{margin:0;min-height:100vh;background:linear-gradient(var(--b1),var(--b2) 55%,var(--b3)) fixed;color:var(--tx);font-family:"Trebuchet MS",system-ui,Roboto,sans-serif;display:flex;justify-content:center}
#app{width:100%;max-width:480px;padding:0 12px 34px}
.hd{background:linear-gradient(var(--rd),#9e0b24);border-radius:0 0 22px 22px;padding:10px 12px 4px;display:flex;align-items:center;gap:8px;box-shadow:0 5px 0 #6e0718;position:relative}
.hd h1{flex:1;margin:0;font-size:24px;color:#ffe27a;text-shadow:0 2px 0 #6e0718;letter-spacing:1px;display:flex;align-items:center;gap:8px}
.hd:after{content:"";position:absolute;left:0;right:0;bottom:-5px;height:0}
.orn{height:18px;background:var(--rd) var(--orn) repeat-x center;border-radius:0 0 10px 10px;margin:0 0 10px;box-shadow:0 3px 0 #6e0718}
.pill,.btn{border:3px solid #b87b00;background:linear-gradient(#fff3b0,#ffd23c);color:#2e1c0e;border-radius:16px;padding:7px 12px;font-weight:800;font-size:15px;cursor:pointer;display:inline-flex;gap:6px;align-items:center;box-shadow:0 3px 0 #b87b00;font-family:inherit}
.pill:active,.btn:active{transform:translateY(3px);box-shadow:none}
.btn.r{background:linear-gradient(#ff6b81,#c8102e);color:#fff;border-color:#7a0a1c;box-shadow:0 3px 0 #7a0a1c}.btn.t{background:linear-gradient(#5fe0d6,#0a9e9a);color:#fff;border-color:#066b68;box-shadow:0 3px 0 #066b68}
.coin{width:22px;height:22px;border-radius:50%;background:radial-gradient(#fff3a0,#e0a100);border:2px solid #9c6b00;display:inline-block}
.cd{background:var(--cd);border:3px solid var(--ac);border-radius:20px;box-shadow:0 5px 0 #b87b00;overflow:hidden;margin-bottom:12px}
.sc svg{display:block;width:100%;height:150px}
.ttl{text-align:center;font-weight:800;color:var(--tx);background:var(--cd);border:3px solid var(--ac);border-radius:14px;padding:6px 10px;margin:10px 0;font-size:14px}
#map{display:grid;grid-template-columns:repeat(5,1fr);gap:7px}
.lv{color:#fff;border:3px solid #fff;border-radius:16px;padding:7px 2px 5px;display:flex;flex-direction:column;align-items:center;cursor:pointer;min-width:0;font-family:inherit;box-shadow:0 4px 0 rgba(0,0,0,.3)}
.lv b{font-size:20px;text-shadow:0 2px 0 rgba(0,0,0,.3)}.lv small{font-size:9px;max-width:100%;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;opacity:.95}.lv i{font-style:normal;font-size:11px;font-weight:800;background:rgba(0,0,0,.3);border-radius:8px;padding:1px 6px;margin-top:2px}
.lv.lk{filter:grayscale(1) brightness(.8);opacity:.75}.lv.nx{filter:none;animation:pl 1.2s infinite;border-color:var(--ac);background:#555!important}
@keyframes pl{50%{transform:scale(1.07)}}
#game,#md,#ld{display:none}
#pb{height:12px;background:rgba(0,0,0,.25);border-radius:8px;overflow:hidden;border:2px solid #fff}#pb i{display:block;height:100%;width:0;background:linear-gradient(90deg,#ffd23c,#ff7b54);transition:.4s}
#gw{position:relative;overflow:hidden;padding:8px 4px;border-radius:18px;background:rgba(255,255,255,.18);min-height:120px}
#grid{display:grid;gap:3px;justify-content:center}
.c{width:var(--cs);height:var(--cs);background:var(--cd);border:2px solid var(--tq);border-radius:8px;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:calc(var(--cs)*.55);box-shadow:0 2px 0 #066b68;color:#2e1c0e}
.c.e{background:none;border:0;box-shadow:none}.c.rv{background:linear-gradient(#fff3a0,#f2b705);border-color:#b87b00;box-shadow:0 2px 0 #b87b00}.c.pop{animation:pop .5s}@keyframes pop{40%{transform:scale(1.35) rotate(-6deg)}}
#eg{position:absolute;left:0;top:0;width:66px;height:44px;z-index:5;cursor:pointer;display:none;filter:drop-shadow(0 3px 2px rgba(0,0,0,.35))}.wg{transform-origin:30px 22px;animation:fl .35s infinite alternate ease-in-out}@keyframes fl{to{transform:scaleY(.2)}}
#gs{display:flex;gap:5px;justify-content:center;margin:10px 0 0;min-height:42px}
#gs span{min-width:34px;height:40px;padding:0 4px;border-radius:12px;background:linear-gradient(#ff6b81,#c8102e);color:#fff;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:900;box-shadow:0 3px 0 #7a0a1c}
#wheel{position:relative;width:250px;height:250px;margin:8px auto;border-radius:50%;background:radial-gradient(circle,#1d3f7a 0,#12285a 62%,#0a9e9a 63%,#0a9e9a 66%,#ffd23c 67%,#ffd23c 71%,#c8102e 72%);touch-action:none;box-shadow:0 6px 0 rgba(0,0,0,.3);user-select:none}
#wheel svg{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
#wheel.sh{animation:sh .4s}@keyframes sh{25%{transform:translateX(-10px)}75%{transform:translateX(10px)}}
.lt{position:absolute;width:50px;height:50px;border-radius:50%;border:3px solid #ffd23c;background:radial-gradient(#fff,#ffeab0);color:#2e1c0e;font-size:24px;font-weight:900;cursor:pointer;font-family:inherit;padding:0;touch-action:none}
.lt.used{background:radial-gradient(#ff8fa0,#c8102e);color:#fff;transform:scale(1.12)}
.acts{display:flex;gap:8px;justify-content:center;margin:8px 0;flex-wrap:wrap}
#md,#ld{position:fixed;inset:0;background:rgba(10,15,40,.7);align-items:center;justify-content:center;z-index:20;padding:16px}
.bx{background:var(--cd);border:4px solid var(--ac);border-radius:24px;padding:20px;max-width:340px;width:100%;text-align:center;box-shadow:0 8px 0 #b87b00}
.bx h3{margin:0 0 8px;color:var(--rd);font-size:26px}.bx p{margin:8px 0}
#ld div{color:#fff;font-weight:800;text-align:center;font-size:17px}#ld .coin{width:50px;height:50px;animation:sp 1s linear infinite}@keyframes sp{to{transform:rotateY(360deg)}}
#ts{position:fixed;left:50%;bottom:26px;transform:translateX(-50%);background:#2e1c0e;color:#ffe27a;padding:10px 18px;border-radius:20px;font-size:15px;font-weight:700;opacity:0;transition:.3s;pointer-events:none;z-index:30;text-align:center;max-width:90%;border:2px solid var(--ac)}#ts.on{opacity:1}
.cf{position:fixed;top:-20px;width:10px;height:14px;z-index:25;animation:fall 2.6s linear forwards;pointer-events:none}@keyframes fall{to{transform:translateY(110vh) rotate(720deg)}}
</style></head><body>
<div id="app">
<div id="home">
 <div class="hd"><h1><svg width="34" height="30" viewBox="-30 -50 60 52"><rect x="-26" y="-18" width="52" height="18" fill="#fff3d6"/><path d="M-30-18Q0-58 30-18Z" fill="#fff8e6" stroke="#6e0718" stroke-width="3"/><rect x="-26" y="-12" width="52" height="5" fill="#ffd23c"/><rect x="-7" y="-16" width="14" height="16" fill="#6e0718"/></svg>АЛТЫН СӨЗ</h1><button class="pill" onclick="shop()"><span class="coin"></span><span id="gold">0</span></button><button class="pill" onclick="toggleMusic()">♪</button></div>
 <div class="orn"></div>
 <div class="cd sc" id="sc"></div>
 <div class="ttl">Кыргыз сөз кроссворду · 30 деңгээл · ар бир деңгээлде жаңы сүрөт</div>
 <div id="map"></div>
</div>
<div id="game">
 <div class="hd"><button class="pill" onclick="home()">←</button><h1 id="gt" style="font-size:17px;justify-content:center"></h1><button class="pill" onclick="shop()"><span class="coin"></span><span id="gold2">0</span></button><button class="pill" onclick="toggleMusic()">♪</button></div>
 <div class="orn"></div>
 <div class="cd sc" id="gsc" style="margin-bottom:8px"></div>
 <div id="pb"><i></i></div>
 <div id="gw"><div id="grid"></div><div id="eg" onpointerdown="eagleTap(event)"><svg viewBox="0 0 60 44" width="66" height="44"><path d="M22 22L4 17V27Z" fill="#3b2412"/><g class="wg"><path d="M24 21Q12-6 0 2Q12 10 20 24Z" fill="#5a3818"/><path d="M34 21Q42-6 58 2Q44 10 38 24Z" fill="#5a3818"/></g><ellipse cx="30" cy="23" rx="11" ry="5.5" fill="#4a2f1a"/><circle cx="41" cy="20" r="4.5" fill="#fff"/><path d="M44 19l8 3-8 3z" fill="#ffb800"/><circle cx="42" cy="19" r="1" fill="#000"/></svg></div></div>
 <div id="gs"></div>
 <div id="wheel"></div>
 <div class="acts"><button class="btn t" id="hb" onclick="hint()">Кеңеш</button><button class="btn r" onclick="send()">Жөнөтүү</button><button class="btn" onclick="undo()">Өчүрүү</button></div>
 <div class="ttl" id="tip">Тамгаларды сүйрөп (же басып) сөз түзүңүз</div>
</div>
</div>
<div id="md"></div><div id="ld"><div><div class="coin"></div><p>Жасалма акыл тамгаларды даярдап жатат…</p></div></div><div id="ts"></div>
<script>
const $=id=>document.getElementById(id),L=30;
const NM=["Ысык-Көл","Ала-Тоо","Бурана","Сон-Көл","Тош-Рабат","Манас","Ала-Арча","Жети-Өгүз","Арсланбап","Чолпон-Ата","Каракол","Ош","Сулайман-Тоо","Нарын","Талас","Баткен","Кара-Балта","Сары-Челек","Кел-Суу","Көк-Бөрү","Боз үй","Комуз","Бүркүт","Ат-Башы","Кочкор","Жалал-Абад","Токтогул","Эр Тоштүк","Теңир-Тоо","Ак-Шыйрак"];
const MK=["Жети өлчөп, бир кес.","Өз үйүм — өлөң төшөгүм.","Ат — жигиттин канаты.","Сабырдын түбү — сары алтын.","Эмгек — эрдин көркү."];
const BANK="ТОО КӨЛ КОМУЗ КЫМЫЗ КҮН КҮЛ КӨК КӨЗ КУШ КУРУТ КАМЫШ КЫЗ КЫР КЫЛ КОЛ КОЙ КАР АТ АТА АЛА АЛМА АЛТЫ АЛТЫН АЛЫС АКЫН АРЫК БАЛА БАЛ БАР БАШ БОЗ БАТА БАТЫР БАЛЫК БҮРКҮТ БҮТҮН ЖЕР ЖЕЛ ЖЫЛ ЖАЗ ЖАЛ ЖАЙ ЖОЛ ЖОРГО ЖЫЛДЫЗ ЖЫЛКЫ ЖАЙЛОО ЛАЧЫН МАЛ МАНАС МУЗ НАРЫН НАН НООРУЗ ОТ ОШ ОРУН ОЮН ӨРҮК ӨЗӨН ӨЛКӨ САЗ САЛ САРЫ СУУ ТАЛААТ ТАЛАА ТАЛ ТАШ ТАН ТОН ТОК ТОГУЗ ТОР ТУУ ТИЛ ТАРАК ТЫЛ УЛАК УЛУУ УКУК УМАЧ ЫР ЫРЧЫ ЫСЫК ЭНЕ ЭЛ ЭШЕК ТОКОЙ КЫРГЫЗ ТОЛУК КАТ ЗАТ КАЗ АЗ ЗАР ЗОК ЗАМАН ЗЫМ ЖЕМИШ ТАРЫ ТЕРЕК ТЕЛЕ КЕЛЕ КЕРЕК КЕЛИН КЕНЕ ЛЕК ЭЛЕК ЭРЕК".split(" ");
let S;try{S=JSON.parse(localStorage.getItem("altyn1"))}catch(e){}S=S||{g:0,u:[1],h:0};
const save=()=>{try{localStorage.setItem("altyn1",JSON.stringify(S))}catch(e){}};
const cost=n=>50*(n-1),rew=n=>15+5*(n-1),mx=()=>Math.max(...S.u);
function toast(t){const e=$("ts");e.textContent=t;e.className="on";clearTimeout(toast.t);toast.t=setTimeout(()=>e.className="",2400)}
function md(h){$("md").innerHTML='<div class="bx">'+h+"</div>";$("md").style.display="flex"}
function cm(){$("md").style.display="none"}
function confetti(){for(let i=0;i<46;i++){const d=document.createElement("div");d.className="cf";d.style.left=Math.random()*100+"vw";d.style.background=["#ffd23c","#c8102e","#0a9e9a","#fff","#ff7b54"][i%5];d.style.animationDelay=Math.random()*.8+"s";document.body.appendChild(d);setTimeout(()=>d.remove(),3800)}}
/* ---------- сүрөттөр ---------- */
const SP=[["#4db8ff","#d8f1ff","#7d9cc4","#4f6f9f","#5aa844"],["#3aa7e8","#bfe8ff","#6f8fb8","#41648f","#3f8f5a"],["#ff7b54","#ffd78a","#9a5b7d","#5c3a66","#7e8f3a"],["#0b1440","#3a2a7a","#3a3f7a","#1c2250","#1f4a3a"],["#ff9a3c","#ffe29a","#8a4a5d","#4d2b4f","#6e7f2e"],["#e84a5f","#ffd36b","#7a3d6b","#432556","#4d7f3a"]];
const spruce=(x,y,s)=>`<polygon fill="#1f6a45" points="${x},${y-30*s} ${x+9*s},${y-16*s} ${x+5*s},${y-16*s} ${x+13*s},${y-4*s} ${x+7*s},${y-4*s} ${x+16*s},${y+10*s} ${x-16*s},${y+10*s} ${x-7*s},${y-4*s} ${x-13*s},${y-4*s} ${x-5*s},${y-16*s} ${x-9*s},${y-16*s}"/>`;
const yurt=(x,y,s,g)=>`<g transform="translate(${x} ${y}) scale(${s})"><rect x="-26" y="-18" width="52" height="18" fill="#f7efdc"/><path d="M-30-18Q0-58 30-18Z" fill="#fbf3e2" stroke="#9a6a3a" stroke-width="2"/><rect x="-26" y="-12" width="52" height="4" fill="#c8102e"/><rect x="-7" y="-16" width="14" height="16" fill="${g?"#ffd23c":"#8a3b2b"}"/><circle cx="0" cy="-42" r="4" fill="none" stroke="#9a6a3a"/></g>`;
function scene(n){const v=n%6,p=SP[v],rr=i=>Math.abs((Math.sin(n*12.9898+i*78.233)*43758.5453)%1),low=v==2||v==4,sx=60+rr(1)*280,sy=low?66:30;
let s=`<svg viewBox="0 0 400 140" preserveAspectRatio="xMidYMid slice"><defs><linearGradient id="s${n}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${p[0]}"/><stop offset="1" stop-color="${p[1]}"/></linearGradient><radialGradient id="r${n}"><stop offset="0" stop-color="#fff6b0"/><stop offset="1" stop-color="#fff6b0" stop-opacity="0"/></radialGradient></defs><rect width="400" height="140" fill="url(#s${n})"/>`;
if(v==3){for(let i=0;i<34;i++)s+=`<circle cx="${rr(i)*400}" cy="${rr(i+50)*75}" r="${.5+rr(i+9)*1.3}" fill="#fff"/>`;s+=`<circle cx="${sx}" cy="30" r="15" fill="#fffbe0"/><circle cx="${sx+7}" cy="27" r="13" fill="${p[0]}"/>`}
else{s+=`<circle cx="${sx}" cy="${sy}" r="38" fill="url(#r${n})"/>`;if(v==5)for(let i=0;i<24;i++){const a=i*Math.PI/12;s+=`<line x1="${sx+19*Math.cos(a)}" y1="${sy+19*Math.sin(a)}" x2="${sx+30*Math.cos(a)}" y2="${sy+30*Math.sin(a)}" stroke="#ffd23c" stroke-width="2.5"/>`}s+=`<circle cx="${sx}" cy="${sy}" r="${v==5?17:14}" fill="#fff3a0"/>`;
for(let i=0;i<3;i++)s+=`<g fill="#fff" opacity=".85"><ellipse cx="${rr(i+3)*330+30}" cy="${14+i*13}" rx="26" ry="7"/><ellipse cx="${rr(i+3)*330+48}" cy="${10+i*13}" rx="16" ry="7"/></g>`}
const mt=(b,h,c,k,sn)=>{let d=`M0 ${b}`,w="";for(let i=0;i<=8;i++){const y=b-h*(.35+.65*rr(k+i));d+=`L${i*50} ${y}`;if(sn&&i>0&&i<8&&y<b-h*.7){const x=i*50;w+=`<path d="M${x} ${y}L${x+13} ${y+15}L${x+5} ${y+9}L${x} ${y+16}L${x-5} ${y+9}L${x-13} ${y+15}Z" fill="#fff"/>`}}return`<path d="${d}L400 ${b}Z" fill="${c}"/>${w}`};
s+=mt(104,78,p[2],10,1)+mt(116,42,p[3],30,0);
if(v==1){s+=`<rect y="108" width="400" height="32" fill="#2b8fd0"/><ellipse cx="${sx}" cy="118" rx="26" ry="4" fill="#fff3a0" opacity=".7"/><path d="M0 116q15-5 30 0t30 0t30 0t30 0t30 0t30 0t30 0t30 0t30 0t30 0t30 0t30 0t30 0M0 128q15-5 30 0t30 0t30 0t30 0t30 0t30 0t30 0t30 0t30 0t30 0t30 0t30 0t30 0" stroke="#fff" fill="none" opacity=".55"/><path d="M0 108Q60 100 120 108V114H0Z" fill="${p[4]}"/>`+yurt(330,112,.8,0)+spruce(30,110,.9)+spruce(52,112,.7)}
else s+=`<path d="M0 118Q100 100 200 116T400 110V140H0Z" fill="${p[4]}"/><path d="M0 130Q120 118 240 130T400 126V140H0Z" fill="#00000022"/>`;
if(v==0)s+=spruce(30,122,1.1)+spruce(58,124,.8)+yurt(300,126,1.1,0)+`<path d="M110 40q5-6 10 0q5-6 10 0M150 56q4-5 8 0q4-5 8 0" stroke="#333" fill="none"/>`;
if(v==2)s+=`<polygon points="275,122 279,56 291,56 295,122" fill="#c98a4b"/><rect x="278" y="44" width="14" height="14" fill="#c98a4b"/><polygon points="277,44 293,44 285,32" fill="#a8693a"/><rect x="283" y="70" width="4" height="12" fill="#5a3818"/>`+spruce(40,124,1)+yurt(150,126,.8,0);
if(v==3)s+=yurt(200,126,1.5,1)+spruce(60,124,1.2)+spruce(340,124,1.2)+spruce(90,126,.8);
if(v==4)s+=`<g transform="translate(160 124)" fill="#2a1a12"><ellipse cx="0" cy="-14" rx="17" ry="7.5"/><path d="M12-16L24-32L29-28L18-12Z"/><ellipse cx="30" cy="-30" rx="6.5" ry="3.5" transform="rotate(30 30 -30)"/><path d="M-14-12L-20 0M-8-9L-9 0M8-9L9 0M14-12L19 0M-16-16Q-26-12-23-3" stroke="#2a1a12" stroke-width="3" fill="none"/><rect x="-3" y="-36" width="7" height="16" rx="3"/><circle cx="0" cy="-40" r="4.5"/><path d="M-5-42L0-52L5-42Z" fill="#fff"/></g>`+spruce(330,124,1.2)+yurt(60,126,.9,0);
if(v==5)s+=yurt(110,126,1.1,0)+yurt(150,128,.8,0)+spruce(320,124,1.1)+spruce(350,126,.8);
return s+"</svg>"}
/* ---------- музыка: комуз ---------- */
let ac,on=true,st=0;const F={x:196,a:220,y:246.9,c:261.6,d:293.7,e:329.6,f:349.2,g:392,A:440,B:493.9,C:523.3};
const PT=("e e . d c . a . . c . d . e . . . g . e . d . c . a . . . . . "+"A . . g e . g . . e . d . c d e . . a . c . d . c . a . . . . . "+"e e . f e . d . . c . d . e . . . A . g . e . d . c . a . . . . . "+"c . d . e . g . . e . d . c . a . . x . a . c . d . c . a . . . . .").split(" ");
function pluck(f,g=.16,d=.8){if(!ac)return;const t=ac.currentTime,o=ac.createOscillator(),o2=ac.createOscillator(),fl=ac.createBiquadFilter(),v=ac.createGain();o.type="sawtooth";o2.type="triangle";o.frequency.value=f;o2.frequency.value=f*2;o2.detune.value=4;fl.type="lowpass";fl.frequency.setValueAtTime(2600,t);fl.frequency.exponentialRampToValueAtTime(500,t+d);v.gain.setValueAtTime(0,t);v.gain.linearRampToValueAtTime(g,t+.01);v.gain.exponentialRampToValueAtTime(.001,t+d);o.connect(fl);o2.connect(fl);fl.connect(v);v.connect(ac.destination);o.start(t);o2.start(t);o.stop(t+d);o2.stop(t+d)}
function initAudio(){if(ac)return;try{ac=new(window.AudioContext||window.webkitAudioContext)();setInterval(()=>{if(!on||ac.state!=="running")return;const k=PT[st%PT.length];if(F[k])pluck(F[k],.17,1.3);if(st%8==0)pluck(110,.09,1.8);st++},240)}catch(e){}}
addEventListener("pointerdown",()=>{initAudio();if(ac&&ac.state==="suspended")ac.resume()});
function toggleMusic(){on=!on;toast(on?"Комуз ойноп жатат ♪":"Үн өчүрүлдү")}
const ok=()=>[523,659,784,1046].forEach((f,i)=>setTimeout(()=>pluck(f,.15,.6),i*110)),bad=()=>pluck(110,.25,.4);
/* ---------- карта ---------- */
function home(){$("game").style.display="none";$("home").style.display="block";$("gold").textContent=S.g;$("sc").innerHTML=scene(mx());const M=$("map");M.innerHTML="";
for(let n=1;n<=L;n++){const o=S.u.includes(n),nx=n===mx()+1,b=document.createElement("button");b.className="lv"+(o?"":nx?" nx":" lk");b.style.background=`linear-gradient(hsl(${n*47%360} 75% 55%),hsl(${n*47%360} 75% 38%))`;b.innerHTML=`<b>${n}</b><small>${NM[n-1]}</small><i>${o?"+"+rew(n):"🔒 "+cost(n)}</i>`;b.onclick=()=>pick(n);M.appendChild(b)}}
function pick(n){if(S.u.includes(n))return play(n);if(n!==mx()+1)return toast("Алгач мурунку деңгээлди ачыңыз");
if(S.g<cost(n))return toast("Алтын жетишпейт: "+cost(n)+" керек, сизде "+S.g);
md(`<h3>${n}-деңгээл</h3><p>«${NM[n-1]}» деңгээлин ачуу үчүн <b>${cost(n)} алтын</b> төлөйсүзбү?</p><div class="acts"><button class="btn r" onclick="pay(${n})">Төлөө</button><button class="btn" onclick="cm()">Жок</button></div>`)}
function pay(n){S.g-=cost(n);S.u.push(n);save();cm();home();play(n)}
function shop(){md(`<h3>Дүкөн</h3><p>Сизде: <b>${S.g}</b> алтын<br>Кошумча кеңеш: <b>${S.h}</b></p><div class="acts"><button class="btn r" onclick="buy()">Кеңеш — 10 алтын</button><button class="btn" onclick="cm()">Жабуу</button></div>`)}
function buy(){if(S.g<10){toast("Алтын жетишпейт");return}S.g-=10;S.h++;save();shop();upd()}
function upd(){$("gold").textContent=S.g;$("gold2").textContent=S.g;if(G)$("hb").textContent="Кеңеш ("+(G.free+S.h)+")"}
/* ---------- ИИ ---------- */
let smp;async function getSample(){if(smp===undefined){try{smp=window.claude&&claude.use?await claude.use("sample"):null}catch(e){smp=null}}return smp}
const okW=w=>/^[А-ЯӨҮҢ]{3,8}$/.test(w);
const sub=(w,b)=>{const m={};for(const c of b)m[c]=(m[c]||0)+1;for(const c of w){if(!m[c])return 0;m[c]--}return 1};
async function gen(n){const len=5+(n>10)+(n>20);let base="",ws=[];const s=await getSample();
if(s){const a=new AbortController(),t=setTimeout(()=>a.abort(),40000);try{const r=await s.json(`You build a Kyrgyz word-wheel game level themed "${NM[n-1]}" (Kyrgyzstan). Choose ONE real Kyrgyz base word of exactly ${len} letters (Cyrillic, UPPERCASE, a noun). Then list 12 other real Kyrgyz words (3 to ${len} letters, UPPERCASE Cyrillic) that can be spelled using ONLY the letters of the base word (no letter used more times than it appears in the base). Random seed ${Math.random()}. Return ONLY JSON: {"base":"...","words":["..."]}`,{cache:false,signal:a.signal,modelTier:"quick"});base=String(r.base).toUpperCase().trim();ws=(r.words||[]).map(x=>String(x).toUpperCase().trim())}catch(e){}finally{clearTimeout(t)}}
if(!okW(base))base="";
if(!base){toast("Жасалма акыл жеткиликсиз — камдалган тамгалар колдонулууда");let best=[];[...BANK].filter(w=>w.length>=5).sort(()=>Math.random()-.5).forEach(b=>{const x=BANK.filter(w=>sub(w,b));if(x.length>best.length){best=x;base=b}});ws=best}
ws=[...new Set([base,...ws])].filter(w=>okW(w)&&sub(w,base));BANK.forEach(w=>{if(ws.length<14&&!ws.includes(w)&&sub(w,base))ws.push(w)});return{base,ws}}
/* ---------- кроссворд ---------- */
function fits(M,w,r,c,d){const dr=d,dc=1-d;let x=0;if(M.has(r-dr+","+(c-dc))||M.has(r+dr*w.length+","+(c+dc*w.length)))return 0;
for(let i=0;i<w.length;i++){const y=r+dr*i,z=c+dc*i,e=M.get(y+","+z);if(e){if(e.ch!==w[i]||e.ds.includes(d))return 0;x++}else if(M.has(y+dc+","+(z+dr))||M.has(y-dc+","+(z-dr)))return 0}return x}
function layout(pool){let best=[];for(let t=0;t<300&&best.length<10;t++){const o=[...pool].sort(()=>Math.random()-.5).sort((a,b)=>(t%3?b.w.length-a.w.length:0)),M=new Map,P=[];
const put=(w,r,c,d)=>{w.r=r;w.c0=c;w.d=d;for(let i=0;i<w.w.length;i++){const k=r+d*i+","+(c+(1-d)*i),e=M.get(k);e?e.ds.push(d):M.set(k,{ch:w.w[i],ds:[d]})}P.push(w)};
put({...o[0]},0,0,0);
for(let i=1;i<o.length&&P.length<10;i++){const w=o[i],C=[];for(const p of P){const d=1-p.d;for(let a=0;a<p.w.length;a++)for(let b=0;b<w.w.length;b++)if(p.w[a]===w.w[b]){const r=p.r+p.d*a-d*b,c=p.c0+(1-p.d)*a-(1-d)*b;if(fits(M,w.w,r,c,d))C.push([r,c,d])}}
if(C.length){const q=C[Math.floor(Math.random()*C.length)];put({...w},q[0],q[1],q[2])}}
if(P.length>best.length)best=P}return best}
/* ---------- оюн ---------- */
let G=null;
async function play(n){$("ld").style.display="flex";const{base,ws}=await gen(n);let P=layout(ws.map(w=>({w})));
const r0=Math.min(...P.map(p=>p.r)),c0=Math.min(...P.map(p=>p.c0));P.forEach(p=>{p.r-=r0;p.c0-=c0;p.keys=[...p.w].map((_,j)=>p.r+p.d*j+","+(p.c0+(1-p.d)*j))});
G={n,base,ws:P,ex:ws.filter(w=>!P.some(p=>p.w===w)),rv:new Set,free:3,gs:[],ls:[...base].sort(()=>Math.random()-.5),el:{},nw:[]};
$("ld").style.display="none";$("home").style.display="none";$("game").style.display="block";$("gt").textContent=n+" · "+NM[n-1];$("gsc").innerHTML=scene(n);drawGrid();wheel();upd();scheduleEagle()}
const done=p=>p.keys.every(k=>G.rv.has(k));
function drawGrid(){const R=Math.max(...G.ws.map(p=>p.r+p.d*(p.w.length-1)))+1,C=Math.max(...G.ws.map(p=>p.c0+(1-p.d)*(p.w.length-1)))+1,cs=Math.max(20,Math.min(42,Math.floor((Math.min(innerWidth,480)-40)/C)-3)),g=$("grid"),LT={};
g.style.setProperty("--cs",cs+"px");g.style.gridTemplateColumns=`repeat(${C},${cs}px)`;g.innerHTML="";G.el={};G.ws.forEach(p=>p.keys.forEach((k,j)=>LT[k]=p.w[j]));G.LT=LT;
for(let r=0;r<R;r++)for(let c=0;c<C;c++){const k=r+","+c,e=document.createElement("div");e.className=LT[k]?"c":"c e";if(LT[k])G.el[k]=e;g.appendChild(e)}paint()}
function paint(){for(const k in G.el){const e=G.el[k],r=G.rv.has(k);e.className="c"+(r?" rv":"")+(G.nw.includes(k)?" pop":"");e.textContent=r?G.LT[k]:""}G.nw=[];const d=G.ws.filter(done).length;$("pb").firstChild.style.width=100*d/G.ws.length+"%";$("tip").textContent=`Табылды: ${d} / ${G.ws.length} сөз`}
function wheel(){const W=$("wheel");W.innerHTML='<svg viewBox="0 0 250 250"><polyline id="ln" fill="none" stroke="#ffd23c" stroke-width="9" stroke-linecap="round" stroke-linejoin="round" opacity=".85"/></svg>';const n=G.ls.length;G.pos=[];
G.ls.forEach((ch,j)=>{const a=-Math.PI/2+2*Math.PI*j/n,x=125+88*Math.cos(a),y=125+88*Math.sin(a),b=document.createElement("button");b.className="lt";b.dataset.j=j;b.textContent=ch;b.style.left=x-25+"px";b.style.top=y-25+"px";G.pos.push([x,y]);W.appendChild(b)});
const c=document.createElement("button");c.className="lt";c.style.cssText="left:100px;top:100px;border-color:#0a9e9a;font-size:22px";c.textContent="⟳";c.onclick=()=>{G.ls.sort(()=>Math.random()-.5);G.gs=[];wheel();guess()};W.appendChild(c);guess()}
function guess(){const e=$("gs");e.innerHTML="";G.gs.forEach(j=>{const s=document.createElement("span");s.textContent=G.ls[j];e.appendChild(s)});document.querySelectorAll("#wheel .lt[data-j]").forEach(b=>b.classList.toggle("used",G.gs.includes(+b.dataset.j)));const l=$("ln");if(l)l.setAttribute("points",G.gs.map(j=>G.pos[j].join(",")).join(" "))}
let dn=0,mv=0;
function hit(b){const j=+b.dataset.j,g=G.gs;if(g[g.length-2]===j&&mv){g.pop()}else if(!g.includes(j)){g.push(j);pluck(F.e,.08,.25)}guess()}
$("wheel").addEventListener("pointerdown",e=>{const b=e.target.closest(".lt[data-j]");if(!b)return;dn=1;mv=0;hit(b)});
$("wheel").addEventListener("pointermove",e=>{if(!dn)return;const x=document.elementFromPoint(e.clientX,e.clientY),b=x&&x.closest&&x.closest(".lt[data-j]");if(b&&(+b.dataset.j!==G.gs[G.gs.length-1])){mv=1;hit(b)}});
addEventListener("pointerup",()=>{if(dn&&mv)send();dn=0});
function undo(){G.gs.pop();guess()}
function send(){if(!G||!G.gs.length)return;const w=G.gs.map(j=>G.ls[j]).join("");G.gs=[];guess();const p=G.ws.find(q=>q.w===w);
if(p&&!done(p)){p.keys.forEach(k=>{if(!G.rv.has(k))G.nw.push(k);G.rv.add(k)});ok();paint();if(G.ws.every(done))setTimeout(win,500)}
else if(p||(G.ws.some(q=>q.w===w)))toast("Бул сөз мурда табылган");
else if(G.ex.includes(w)){G.ex=G.ex.filter(x=>x!==w);S.g+=2;save();upd();ok();toast("Бонус сөз «"+w+"»! +2 алтын")}
else{bad();const e=$("wheel");e.classList.add("sh");setTimeout(()=>e.classList.remove("sh"),420)}}
function hint(){const u=G.ws.filter(p=>!done(p));if(!u.length)return;if(G.free>0)G.free--;else if(S.h>0){S.h--;save()}else return toast("Кеңеш түгөндү — дүкөндөн алыңыз");
const p=u[Math.floor(Math.random()*u.length)],r=p.keys.filter(k=>!G.rv.has(k)),k=r[Math.floor(Math.random()*r.length)];G.rv.add(k);G.nw.push(k);pluck(F.A,.15,.5);upd();paint();if(G.ws.every(done))setTimeout(win,500)}
function win(){const n=G.n,r=rew(n);S.g+=r;save();upd();ok();confetti();const can=n<L&&S.u.includes(n+1);
md(`<h3>${n===L?"Чемпион!":"Азаматсыз!"}</h3><p>Сиз <b>+${r} алтын</b> таптыңыз!</p><p style="color:var(--mu);font-style:italic">${MK[Math.floor(Math.random()*MK.length)]}</p><div class="acts">${can?`<button class="btn t" onclick="cm();play(${n+1})">Кийинки</button>`:""}<button class="btn r" onclick="cm();play(${n})">Кайра ойноо</button><button class="btn" onclick="cm();home()">Карта</button></div>`)}
/* ---------- бүркүт ---------- */
let eT,eOn=0;
function scheduleEagle(){clearTimeout(eT);eT=setTimeout(fly,5000+Math.random()*5000)}
function fly(){scheduleEagle();if(!G||$("game").style.display!=="block"||eOn)return;const w=$("gw"),e=$("eg"),W=w.clientWidth,H=w.clientHeight,l=Math.random()<.5,y0=Math.random()*(H-50),y1=Math.random()*(H-50);
e.style.display="block";e.style.opacity=1;eOn=1;e.firstChild.style.transform=l?"none":"scaleX(-1)";
const a=e.animate([{transform:`translate(${l?-80:W+14}px,${y0}px)`},{transform:`translate(${W/2-33}px,${(y0+y1)/2-18}px)`},{transform:`translate(${l?W+14:-80}px,${y1}px)`}],{duration:4800,easing:"ease-in-out"});a.onfinish=()=>{e.style.display="none";eOn=0}}
function eagleTap(ev){ev.stopPropagation();if(!eOn)return;const e=$("eg");S.g+=3;save();upd();ok();toast("Бүркүт алтын ташты! +3 алтын");e.style.opacity=0;e.getAnimations().forEach(a=>a.finish())}
home();
</script></body></html>
