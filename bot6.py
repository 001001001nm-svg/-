import os, re, json, time, mimetypes, urllib.request, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", 10000))
ST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
KEY = os.environ.get("GEMINI_API_KEY", "")  # ачкычты Render > Environment ичине сал, кодго жазба
MODELS = [m for m in [os.environ.get("GEMINI_MODEL"), "gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash"] if m]
HITS = []


def ai_level(n, ln, theme, avoid):
    prompt = ("Kyrgyz word-wheel game. Theme: %s (Kyrgyzstan). Level %s. Choose ONE common real Kyrgyz noun of exactly %d letters "
              "(Cyrillic, UPPERCASE) as BASE, not in this list: [%s]. Then list 14 other real Kyrgyz words (3 to %d letters, "
              "UPPERCASE Cyrillic) spelled ONLY with letters of BASE (each letter at most as many times as in BASE). "
              'Return ONLY JSON: {"base":"...","words":["..."]}') % (theme, n, ln, avoid, ln)
    body = json.dumps({"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                       "generationConfig": {"responseMimeType": "application/json", "temperature": 1.2}}).encode()
    err = RuntimeError("no model")
    for m in MODELS:
        try:
            req = urllib.request.Request(
                "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % m, body,
                {"Content-Type": "application/json", "x-goog-api-key": KEY})
            r = json.load(urllib.request.urlopen(req, timeout=30))
            parts = r["candidates"][0]["content"]["parts"]
            t = "".join(x.get("text", "") for x in parts)
            return json.loads(re.sub(r"```(json)?", "", t).strip())
        except Exception as e:
            err = e
    raise err


HTML = r"""<!DOCTYPE html>
<html lang="ky"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Алтын Сөз</title>
<style>
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;height:100%}
body{background:#7aa6d8;font-family:"Trebuchet MS",system-ui,sans-serif;color:#fff;overflow-x:hidden}
#bg{position:fixed;inset:0;z-index:0}#bg svg,#bg img{position:absolute;inset:0;width:100%;height:100%}#bg img{object-fit:cover;object-position:center bottom}
#bg:after{content:"";position:absolute;inset:0;background:linear-gradient(rgba(20,10,40,.35),transparent 32%,transparent 62%,rgba(0,0,0,.35))}
#fx{position:fixed;inset:0;z-index:6;pointer-events:none}#fx>div{position:absolute;left:0;top:0;pointer-events:auto;display:none;cursor:pointer;filter:drop-shadow(0 4px 3px rgba(0,0,0,.4))}
#app{position:relative;z-index:2;max-width:480px;margin:0 auto;min-height:100dvh;padding:calc(10px + env(safe-area-inset-top)) 12px calc(14px + env(safe-area-inset-bottom));display:flex;flex-direction:column}
#menu,#game{flex:1;display:flex;flex-direction:column}#game{display:none}
.top{display:flex;gap:8px;align-items:center}
.pl{background:rgba(25,30,55,.72);border:2px solid rgba(255,255,255,.35);border-radius:22px;padding:5px 14px;font-weight:800;font-size:17px;display:flex;gap:6px;align-items:center}
.ic{width:46px;height:46px;border-radius:50%;border:2px solid rgba(255,255,255,.4);background:rgba(25,30,55,.78);color:#fff;font-size:22px;cursor:pointer;position:relative;padding:0}
.ic small{position:absolute;right:-4px;bottom:-4px;background:#ff8a2a;border-radius:10px;font-size:12px;padding:1px 6px}
.logo{text-align:center;font:400 52px/1.05 Georgia,"Times New Roman",serif;margin:40px 0 0;text-shadow:0 3px 8px rgba(0,0,0,.4);letter-spacing:2px}.logo small{display:block;font-size:32px;letter-spacing:8px}
#circ{width:210px;height:210px;border-radius:50%;margin:auto;background:rgba(255,255,255,.28);display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:0 0 0 10px rgba(255,255,255,.12)}
#circ b{font-size:64px;text-shadow:0 3px 6px rgba(0,0,0,.3)}#circ span{font-size:22px;font-weight:800;text-transform:uppercase;text-shadow:0 2px 4px rgba(0,0,0,.45);text-align:center;padding:0 10px}
.bot{padding-bottom:64px}
.gb,.kb{display:block;width:90%;margin:0 auto 14px;border:0;border-radius:40px;padding:20px 10px;font:800 28px "Trebuchet MS",system-ui,sans-serif;color:#fff;cursor:pointer;text-shadow:0 2px 3px rgba(0,0,0,.35);position:relative}
.gb{background:linear-gradient(#69c93a,#43a42b);box-shadow:0 6px 0 #2e7d1d,0 10px 16px rgba(0,0,0,.3)}
.kb{background:#161a2b;font-size:20px;padding:19px 10px;box-shadow:0 6px 0 #070914,0 10px 16px rgba(0,0,0,.3)}
.kb em{position:absolute;right:14px;top:50%;transform:translateY(-50%);background:#fff;color:#222;border-radius:8px;font-style:normal;font-size:18px;padding:5px 11px;text-shadow:none}
.gb:active,.kb:active{transform:translateY(4px)}
.wh{position:fixed;right:max(14px,calc(50% - 226px));bottom:calc(14px + env(safe-area-inset-bottom));width:66px;height:66px;border-radius:50%;border:4px solid #5b4fcf;background:conic-gradient(#ff4d6d 0 60deg,#ffd23c 60deg 120deg,#4dd0e1 120deg 180deg,#7bd957 180deg 240deg,#b388ff 240deg 300deg,#ff9f1c 300deg 360deg);box-shadow:0 4px 10px rgba(0,0,0,.4);z-index:3;cursor:pointer}
#pb{height:10px;background:rgba(0,0,0,.35);border-radius:6px;overflow:hidden;margin:10px 0 8px}#pb i{display:block;height:100%;width:0;background:linear-gradient(90deg,#ffd23c,#ff7b54);transition:.4s}
#gw{flex:1;display:flex;align-items:center;justify-content:center;background:rgba(15,20,45,.45);backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px);border-radius:22px;padding:10px 4px;min-height:140px}
#grid{display:grid;gap:3px}
.c{width:var(--cs);height:var(--cs);border-radius:7px;background:#f6ecd3;border:2px solid #d6c18f;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:calc(var(--cs)*.58);color:#fff;text-shadow:0 2px 2px rgba(0,0,0,.35);box-shadow:0 2px 0 #b79e66}
.c.e{background:none;border:0;box-shadow:none}.c.rv{background:linear-gradient(#7bd957,#3fa32a);border-color:#2e7d1d;box-shadow:0 2px 0 #1f5a14}.c.pop{animation:pop .5s}@keyframes pop{40%{transform:scale(1.35) rotate(-6deg)}}
#gs{display:flex;gap:5px;justify-content:center;margin:10px 0 0;min-height:42px}
#gs span{min-width:32px;height:38px;padding:0 4px;border-radius:12px;background:linear-gradient(#ff9a3c,#e25a1a);display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:900;box-shadow:0 3px 0 #9a3a0c}
.wr{display:flex;align-items:center;justify-content:center;gap:8px;margin:6px 0 4px}
#wheel{position:relative;width:220px;height:220px;border-radius:50%;background:rgba(255,255,255,.9);touch-action:none;user-select:none;box-shadow:0 6px 18px rgba(0,0,0,.4)}
#wheel svg{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
#wheel.sh{animation:sh .4s}@keyframes sh{25%{transform:translateX(-10px)}75%{transform:translateX(10px)}}
.lt{position:absolute;width:46px;height:46px;border-radius:50%;border:0;background:none;color:#2b2540;font:800 30px "Trebuchet MS",sans-serif;padding:0;cursor:pointer;touch-action:none}
.lt.used{background:#ff8a2a;color:#fff;transform:scale(1.1)}.lt.sf{left:88px;top:88px;width:44px;height:44px;font-size:24px;background:#e4e0ee}
#md,#ld{position:fixed;inset:0;z-index:20;background:rgba(10,15,40,.7);display:none;align-items:center;justify-content:center;padding:16px}
.bx{background:#fff8e6;color:#2e1c0e;border:4px solid #f2b705;border-radius:24px;padding:20px;max-width:340px;width:100%;text-align:center;box-shadow:0 8px 0 #b87b00}.bx h3{margin:0 0 8px;color:#c8102e;font-size:26px}.bx p{margin:8px 0}
.mb{display:block;width:100%;margin:8px 0 0;border:0;border-radius:22px;padding:13px;font:800 17px "Trebuchet MS",sans-serif;background:linear-gradient(#69c93a,#43a42b);color:#fff;box-shadow:0 4px 0 #2e7d1d;cursor:pointer}.mb.d{background:#161a2b;box-shadow:0 4px 0 #070914}.mb.r{background:linear-gradient(#ff6b81,#c8102e);box-shadow:0 4px 0 #7a0a1c}
#fw{width:190px;height:190px;border-radius:50%;margin:12px auto;border:6px solid #f2b705;background:conic-gradient(#ff4d6d 0 60deg,#ffd23c 60deg 120deg,#4dd0e1 120deg 180deg,#7bd957 180deg 240deg,#b388ff 240deg 300deg,#ff9f1c 300deg 360deg);transition:transform 3s cubic-bezier(.2,.8,.2,1);position:relative}
#fwp{text-align:center;font-size:30px;margin-bottom:-26px;position:relative;z-index:1}
#ld div{font-weight:800;text-align:center;font-size:18px}
#ts{position:fixed;left:50%;bottom:90px;transform:translateX(-50%);background:#2e1c0e;color:#ffe27a;padding:10px 18px;border-radius:20px;font-size:15px;font-weight:700;opacity:0;transition:.3s;pointer-events:none;z-index:30;text-align:center;max-width:90%;border:2px solid #f2b705}#ts.on{opacity:1}
.cf{position:fixed;top:-20px;width:10px;height:14px;z-index:25;animation:fall 2.6s linear forwards;pointer-events:none}@keyframes fall{to{transform:translateY(110vh) rotate(720deg)}}
.wg{transform-origin:30px 22px;animation:fl .35s infinite alternate ease-in-out}@keyframes fl{to{transform:scaleY(.2)}}
.lg{fill:#d7dbe2;stroke:#8a93a0;stroke-width:1.5;transform-box:fill-box;transform-origin:50% 0;animation:wk .4s infinite alternate ease-in-out}.lg:nth-child(odd){animation-delay:-.4s}@keyframes wk{from{transform:rotate(-26deg)}to{transform:rotate(26deg)}}
</style></head><body>
<div id="bg"></div>
<div id="fx">
<div id="eg" onpointerdown="tapFx(event,3)"><svg viewBox="0 0 60 44" width="92" height="68"><path d="M22 22L4 17V27Z" fill="#3b2412"/><g class="wg"><path d="M24 21Q12-6 0 2Q12 10 20 24Z" fill="#5a3818"/><path d="M34 21Q42-6 58 2Q44 10 38 24Z" fill="#5a3818"/></g><ellipse cx="30" cy="23" rx="11" ry="5.5" fill="#4a2f1a"/><circle cx="41" cy="20" r="4.5" fill="#fff"/><path d="M44 19l8 3-8 3z" fill="#ffb800"/><circle cx="42" cy="19" r="1" fill="#000"/></svg></div>
<div id="lp" onpointerdown="tapFx(event,5)"><svg viewBox="0 0 130 64" width="160" height="79"><g><rect class="lg" x="30" y="38" width="8" height="22" rx="4"/><rect class="lg" x="42" y="38" width="8" height="22" rx="4"/><rect class="lg" x="88" y="38" width="8" height="22" rx="4"/><rect class="lg" x="100" y="38" width="8" height="22" rx="4"/></g><path d="M26 34Q-2 34 4 10Q6 2 14 6" fill="none" stroke="#c9ced6" stroke-width="8" stroke-linecap="round"/><path d="M26 34Q-2 34 4 10Q6 2 14 6" fill="none" stroke="#4a5260" stroke-width="8" stroke-dasharray="4 7"/><ellipse cx="64" cy="34" rx="42" ry="15" fill="#dfe3e8" stroke="#8a93a0" stroke-width="2"/><g fill="#4a5260" opacity=".85"><circle cx="38" cy="30" r="4"/><circle cx="52" cy="25" r="3.5"/><circle cx="66" cy="31" r="4.5"/><circle cx="80" cy="26" r="3.5"/><circle cx="92" cy="33" r="3.5"/><circle cx="48" cy="38" r="3"/><circle cx="74" cy="40" r="3"/></g><circle cx="112" cy="26" r="12" fill="#e8ebf0" stroke="#8a93a0" stroke-width="2"/><path d="M104 17l2-10 7 7zM116 15l5-9 4 10z" fill="#c9ced6"/><circle cx="116" cy="24" r="2" fill="#222"/><ellipse cx="122" cy="30" rx="3" ry="2" fill="#ee8899"/></svg></div>
</div>
<input type="file" id="mf" accept="audio/*" hidden>
<div id="app">
<div id="menu">
 <div class="top"><div class="pl">💎 <b id="g1"></b></div><div class="pl"><span style="color:#6fc3ff">Ө</span> <b id="bw1"></b></div><i style="flex:1"></i><div class="pl">🔥 <b id="sk"></b></div><button class="ic" onclick="sett()">⚙</button></div>
 <h1 class="logo"><small>АЛТЫН</small>СӨЗДӨР</h1>
 <div id="circ"><b id="cn"></b><span id="cl"></span></div>
 <div class="bot"><button class="gb" onclick="play(S.u)">ДЕҢГЭЭЛ <span id="gn"></span></button><button class="kb" onclick="daily()">КҮНДҮН КРОССВОРДУ<em id="dt"></em></button></div>
 <button class="wh" onclick="wheelM()"></button>
</div>
<div id="game">
 <div class="top"><button class="ic" onclick="home()">←</button><div class="pl" style="flex:1;justify-content:center" id="gt"></div><div class="pl">💎 <b id="g2"></b></div></div>
 <div id="pb"><i></i></div>
 <div id="gw"><div id="grid"></div></div>
 <div id="gs"></div>
 <div class="wr"><button class="ic" style="width:54px;height:54px" onclick="hint()">💡<small>10</small></button><div id="wheel"></div><button class="ic" style="width:54px;height:54px" onclick="bonus()">📖<small id="bc">0</small></button></div>
</div>
</div>
<div id="md"></div><div id="ld"><div>Жасалма акыл сөздөрдү даярдап жатат…</div></div><div id="ts"></div>
<script>
const $=id=>document.getElementById(id);
const NM=["Сон-Көл","Ысык-Көл","Ала-Арча","Тош-Рабат","Бурана","Сулайман-Тоо","Чолпон-Ата","Жети-Өгүз","Арсланбап","Каракол","Нарын","Талас"];
const MK=["Жети өлчөп, бир кес.","Өз үйүм — өлөң төшөгүм.","Ат — жигиттин канаты.","Сабырдын түбү — сары алтын.","Эмгек — эрдин көркү."];
const BANK="ТОО КӨЛ КОМУЗ КЫМЫЗ КҮН КҮЛ КӨК КӨЗ КУШ КУРУТ КАМЫШ КЫЗ КЫР КЫЛ КОЛ КОЙ КАР АТ АТА АЛА АЛМА АЛТЫ АЛТЫН АЛЫС АКЫН АРЫК БАЛА БАЛ БАР БАШ БОЗ БАТА БАТЫР БАЛЫК БҮРКҮТ БҮТҮН ЖЕР ЖЕЛ ЖЫЛ ЖАЗ ЖАЛ ЖАЙ ЖОЛ ЖОРГО ЖЫЛДЫЗ ЖЫЛКЫ ЖАЙЛОО ЛАЧЫН МАЛ МАНАС МУЗ НАРЫН НАН НООРУЗ ОТ ОШ ОРУН ОЮН ӨРҮК ӨЗӨН ӨЛКӨ САЗ САЛ САРЫ СУУ ТАЛААТ ТАЛАА ТАЛ ТАШ ТАН ТОН ТОК ТОГУЗ ТОР ТУУ ТИЛ ТАРАК ТЫЛ УЛАК УЛУУ УКУК УМАЧ ЫР ЫРЧЫ ЫСЫК ЭНЕ ЭЛ ЭШЕК ТОКОЙ КЫРГЫЗ ТОЛУК КАТ ЗАТ КАЗ АЗ ЗАР ЗОК ЗАМАН ЗЫМ ЖЕМИШ ТАРЫ ТЕРЕК ТЕЛЕ КЕЛЕ КЕРЕК КЕЛИН КЕНЕ ЛЕК ЭЛЕК ЭРЕК".split(" ");
const td=()=>new Date().toISOString().slice(0,10);
let S={g:100,u:1,b:[],c:{},bw:0,s:0,ld:"",w:"",d:""};
try{Object.assign(S,JSON.parse(localStorage.getItem("altyn2")))}catch(e){}
const save=()=>{try{localStorage.setItem("altyn2",JSON.stringify(S))}catch(e){}};
const vy=n=>((n-1)/5|0)%NM.length,loc=n=>NM[vy(n)];
function toast(t){const e=$("ts");e.textContent=t;e.className="on";clearTimeout(toast.t);toast.t=setTimeout(()=>e.className="",2400)}
function modal(h){$("md").innerHTML='<div class="bx">'+h+"</div>";$("md").style.display="flex"}
function cm(){$("md").style.display="none"}
function confetti(){for(let i=0;i<46;i++){const d=document.createElement("div");d.className="cf";d.style.left=Math.random()*100+"vw";d.style.background=["#ffd23c","#c8102e","#0a9e9a","#fff","#ff7b54"][i%5];d.style.animationDelay=Math.random()*.8+"s";document.body.appendChild(d);setTimeout(()=>d.remove(),3800)}}
function upd(){const n=S.u;$("g1").textContent=S.g;$("g2").textContent=S.g;$("bw1").textContent=S.bw;$("sk").textContent=S.s;$("gn").textContent=n;$("cn").textContent=n;$("cl").textContent=loc(n);$("dt").textContent=S.d===td()?"✓":new Date().getDate();if(G)$("bc").textContent=G.bws.length}
/* ---------- фон: сүрөт же пейзаж ---------- */
const PL=[["#1e90ff","#bfe8ff","#8fb3e0","#5b7fc2","#4fc24a"],["#ff7a18","#ffd27a","#c0587a","#7a3a7a","#9ac03a"],["#ee3a7a","#ffc890","#9a3f8a","#5a2a7a","#5ac04a"],["#0a7be0","#e2f8ff","#7aa6d8","#4a76b8","#2fb36f"],["#08103a","#6a3fa0","#3a3f8a","#232a6a","#1f6a4a"],["#ff5e62","#ffe08a","#b35c9c","#7a3f8c","#a6c63b"]];
const spr=(x,y,s)=>`<path fill="#1f6a45" d="M${x} ${y-30*s}l${14*s} ${30*s}h${-8*s}l${12*s} ${22*s}h${-36*s}l${12*s} ${-22*s}h${-8*s}z"/>`;
const yurt=(x,y,s)=>`<g transform="translate(${x} ${y}) scale(${s})"><rect x="-26" y="-18" width="52" height="18" fill="#f7efdc"/><path d="M-30-18Q0-58 30-18Z" fill="#fbf3e2" stroke="#9a6a3a" stroke-width="2"/><rect x="-26" y="-12" width="52" height="4" fill="#c8102e"/><rect x="-7" y="-16" width="14" height="16" fill="#8a3b2b"/></g>`;
function scene(k){const p=PL[k%6],r=i=>Math.abs((Math.sin(k*12.99+i*78.2)*43758.5)%1);
let s=`<svg viewBox="0 0 400 800" preserveAspectRatio="xMidYMax slice"><defs><linearGradient id="a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${p[0]}"/><stop offset=".62" stop-color="${p[1]}"/></linearGradient><linearGradient id="b" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${p[4]}"/><stop offset="1" stop-color="#1d6a3a"/></linearGradient></defs><rect width="400" height="800" fill="url(#a)"/><circle cx="${70+r(1)*260}" cy="${k%6==4?150:260}" r="48" fill="#fff6b0" opacity=".9"/>`;
if(k%6==4)for(let i=0;i<50;i++)s+=`<circle cx="${r(i)*400}" cy="${r(i+60)*420}" r="${.6+r(i+9)*1.4}" fill="#fff"/>`;
const mt=(b,h,c,q)=>{let d=`M0 ${b}`,w="";for(let i=0;i<=8;i++){const y=b-h*(.35+.65*r(q+i));d+=`L${i*50} ${y}`;if(q<20&&i&&i<8&&y<b-h*.7)w+=`<path d="M${i*50} ${y}l20 26-12-8-8 12-8-12-12 8z" fill="#fff"/>`}return`<path d="${d}L400 ${b}Z" fill="${c}"/>${w}`};
s+=mt(560,280,p[2],10)+mt(590,140,p[3],30)+`<path d="M0 590Q120 560 220 585T400 575V800H0Z" fill="url(#b)"/>`;
for(let i=0;i<45;i++)s+=`<circle cx="${r(i+80)*400}" cy="${620+r(i+120)*180}" r="${1.5+r(i+7)*2.5}" fill="${["#ff4d6d","#ffd23c","#fff","#ff9f1c","#b388ff"][i%5]}"/>`;
return s+spr(40,640,1.8)+spr(92,655,1.2)+yurt(300,660,1.9)+"</svg>"}
function setBg(k){if(setBg.k===k)return;setBg.k=k;$("bg").innerHTML=scene(k)+`<img src="/f/v${k}.jpg" onerror="this.remove()">`}
/* ---------- музыка ---------- */
let ac,on=true,ms=0,au=null,real=false;const F={a:110,b:165,e:329.6,g:392,A:440,c:261.6,d:293.7,C:523.3,D:587.3,E:659.3};
const PT=("A . A g e . g . e . d . c . d . e . e g A . g . e . d . c . a . c . d . e . g . A . g . e . d c D . C . A . g . e . g . A . . . E . D C A . C . A . g . e . d . e g A . A g e . d . c . a . . .").split(" ");
function pluck(f,g=.16,d=.8){if(!ac)return;const t=ac.currentTime,o=ac.createOscillator(),o2=ac.createOscillator(),fl=ac.createBiquadFilter(),v=ac.createGain();o.type="sawtooth";o2.type="triangle";o.frequency.setValueAtTime(f*1.012,t);o.frequency.exponentialRampToValueAtTime(f,t+.04);o2.frequency.value=f*2;fl.type="lowpass";fl.frequency.setValueAtTime(3200,t);fl.frequency.exponentialRampToValueAtTime(450,t+d);v.gain.setValueAtTime(0,t);v.gain.linearRampToValueAtTime(g,t+.008);v.gain.exponentialRampToValueAtTime(.001,t+d);o.connect(fl);o2.connect(fl);fl.connect(v);v.connect(ac.destination);o.start(t);o2.start(t);o.stop(t+d);o2.stop(t+d)}
const idb=(m,v)=>new Promise(r=>{try{const q=indexedDB.open("alt",1);q.onupgradeneeded=()=>q.result.createObjectStore("s");q.onsuccess=()=>{const t=q.result.transaction("s",m=="get"?"readonly":"readwrite").objectStore("s"),x=m=="get"?t.get("m"):t.put(v,"m");x.onsuccess=()=>r(x.result);x.onerror=()=>r()};q.onerror=()=>r()}catch(e){r()}});
function setAu(u){if(au)au.pause();au=new Audio(u);au.loop=true;au.volume=.75;real=true;if(on)au.play().catch(()=>{})}
async function loadMus(){const b=await idb("get");if(b)return setAu(URL.createObjectURL(b));try{const r=await fetch("/f/music.mp3",{method:"HEAD"});if(r.ok)setAu("/f/music.mp3")}catch(e){}}
function initAudio(){if(ac)return;try{ac=new(window.AudioContext||window.webkitAudioContext)()}catch(e){}loadMus();setInterval(()=>{if(!on||real||!ac||ac.state!=="running")return;const k=PT[ms%PT.length];if(F[k])pluck(F[k],.17,.9);if(ms%2==0)pluck(220,.035,.15);if(ms%4==0)pluck(F.a,.1,.6);if(ms%4==2)pluck(F.b,.06,.4);ms++},170)}
addEventListener("pointerdown",()=>{initAudio();if(ac&&ac.state==="suspended")ac.resume();if(au&&on&&au.paused)au.play().catch(()=>{})});
function toggleMusic(){on=!on;if(au){on?au.play().catch(()=>{}):au.pause()}toast(on?"Музыка күйдү ♪":"Үн өчүрүлдү")}
$("mf").onchange=async e=>{const f=e.target.files[0];if(!f)return;await idb("put",f);setAu(URL.createObjectURL(f));toast("Сиздин музыка коюлду ♪")};
const ok=()=>[523,659,784,1046].forEach((f,i)=>setTimeout(()=>pluck(f,.15,.6),i*110)),bad=()=>pluck(110,.25,.4);
/* ---------- меню ---------- */
function home(){$("game").style.display="none";$("menu").style.display="flex";G=null;setBg(vy(S.u));upd()}
function sett(){modal(`<h3>Жөндөөлөр</h3><button class="mb" onclick="toggleMusic();sett()">Музыка: ${on?"күйгүзүлгөн":"өчүрүлгөн"}</button><button class="mb" onclick="$('mf').click()">🎵 Өз музыкамды кошуу</button><button class="mb r" onclick="if(confirm('Прогрессти өчүрөбү?')){localStorage.removeItem('altyn2');location.reload()}">Баштан баштоо</button><button class="mb d" onclick="cm()">Жабуу</button>`)}
function wheelM(){if(S.w===td())return toast("Дөңгөлөк эртең кайра!");modal(`<h3>Алтын дөңгөлөк</h3><div id="fwp">▼</div><div id="fw"></div><button class="mb" id="sb" onclick="spin()">АЙЛАНТУУ</button>`)}
const PZ=[10,20,5,50,30,100];
function spin(){const d=1440+(Math.random()*360|0),i=(((360-d%360)%360)/60)|0;$("sb").disabled=true;$("fw").style.transform=`rotate(${d}deg)`;setTimeout(()=>{S.g+=PZ[i];S.w=td();save();upd();ok();$("sb").outerHTML=`<p><b>+${PZ[i]} 💎</b></p><button class="mb d" onclick="cm()">Жабуу</button>`},3200)}
function daily(){if(S.d===td())return toast("Бүгүнкү кроссворд чечилди ✓");play(1000+((Date.now()/864e5|0)%9000),1)}
/* ---------- сөздөр (ИИ же камдалган тизме) ---------- */
const okW=w=>/^[А-ЯӨҮҢ]{3,8}$/.test(w);
const sub=(w,b)=>{const m={};for(const c of b)m[c]=(m[c]||0)+1;for(const c of w){if(!m[c])return 0;m[c]--}return 1};
async function gen(n,len){if(S.c[n])return S.c[n];let base="",ws=[];
try{const a=new AbortController(),t=setTimeout(()=>a.abort(),30000);const r=await(await fetch(`/api/level?n=${n}&len=${len}&theme=${encodeURIComponent(loc(n))}&avoid=${encodeURIComponent(S.b.slice(-40).join(","))}`,{signal:a.signal})).json();clearTimeout(t);base=String(r.base||"").toUpperCase().trim();ws=(r.words||[]).map(x=>String(x).toUpperCase().trim())}catch(e){}
if(!okW(base)||base.length<5||S.b.includes(base))base="";
ws=[...new Set([base,...ws])].filter(w=>base&&okW(w)&&sub(w,base));
if(!base||ws.length<7){const cd=[...new Set(BANK.filter(w=>w.length>=5))].map(b=>[b,BANK.filter(w=>sub(w,b))]).filter(x=>x[1].length>=4).sort((a,b)=>b[1].length-a[1].length),i0=(n-1)%cd.length,x=cd.find((c,i)=>i>=i0&&!S.b.includes(c[0]))||cd[i0];base=x[0];ws=x[1]}
S.c[n]={base,ws};S.b.push(base);save();return S.c[n]}
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
async function play(n,dl){$("ld").style.display="flex";const len=dl?7:5+(n>15)+(n>40),{base,ws}=await gen(n,len);const P=layout(ws.map(w=>({w})));
const r0=Math.min(...P.map(p=>p.r)),c0=Math.min(...P.map(p=>p.c0));P.forEach(p=>{p.r-=r0;p.c0-=c0;p.keys=[...p.w].map((_,j)=>p.r+p.d*j+","+(p.c0+(1-p.d)*j))});
G={n,dl,base,ws:P,ex:ws.filter(w=>!P.some(p=>p.w===w)),rv:new Set,gs:[],ls:[...base].sort(()=>Math.random()-.5),el:{},nw:[],bws:[]};
$("ld").style.display="none";$("menu").style.display="none";$("game").style.display="flex";$("gt").textContent=dl?"Күндүн кроссворду":n+" · "+loc(n);setBg(dl?5:vy(n));drawGrid();mkWheel();upd()}
const done=p=>p.keys.every(k=>G.rv.has(k));
function drawGrid(){const R=Math.max(...G.ws.map(p=>p.r+p.d*(p.w.length-1)))+1,C=Math.max(...G.ws.map(p=>p.c0+(1-p.d)*(p.w.length-1)))+1,cs=Math.max(18,Math.min(40,Math.floor((Math.min(innerWidth,480)-48)/C)-3,Math.floor((innerHeight-470)/R)-3)),g=$("grid"),LT={};
g.style.setProperty("--cs",cs+"px");g.style.gridTemplateColumns=`repeat(${C},${cs}px)`;g.innerHTML="";G.el={};G.ws.forEach(p=>p.keys.forEach((k,j)=>LT[k]=p.w[j]));G.LT=LT;
for(let r=0;r<R;r++)for(let c=0;c<C;c++){const k=r+","+c,e=document.createElement("div");e.className=LT[k]?"c":"c e";if(LT[k])G.el[k]=e;g.appendChild(e)}paint()}
function paint(){for(const k in G.el){const e=G.el[k],r=G.rv.has(k);e.className="c"+(r?" rv":"")+(G.nw.includes(k)?" pop":"");e.textContent=r?G.LT[k]:""}G.nw=[];$("pb").firstChild.style.width=100*G.ws.filter(done).length/G.ws.length+"%"}
function mkWheel(){const W=$("wheel");W.innerHTML='<svg viewBox="0 0 220 220"><polyline id="ln" fill="none" stroke="#ff8a2a" stroke-width="10" stroke-linecap="round" stroke-linejoin="round" opacity=".7"/></svg>';const n=G.ls.length;G.pos=[];
G.ls.forEach((ch,j)=>{const a=-Math.PI/2+2*Math.PI*j/n,x=110+76*Math.cos(a),y=110+76*Math.sin(a),b=document.createElement("button");b.className="lt";b.dataset.j=j;b.textContent=ch;b.style.left=x-23+"px";b.style.top=y-23+"px";G.pos.push([x,y]);W.appendChild(b)});
const c=document.createElement("button");c.className="lt sf";c.textContent="⟳";c.onclick=()=>{G.ls.sort(()=>Math.random()-.5);G.gs=[];mkWheel()};W.appendChild(c);guess()}
function guess(){const e=$("gs");e.innerHTML="";G.gs.forEach(j=>{const s=document.createElement("span");s.textContent=G.ls[j];e.appendChild(s)});document.querySelectorAll("#wheel .lt[data-j]").forEach(b=>b.classList.toggle("used",G.gs.includes(+b.dataset.j)));const l=$("ln");if(l)l.setAttribute("points",G.gs.map(j=>G.pos[j].join(",")).join(" "))}
let dn=0,mv=0;
function hit(b){const j=+b.dataset.j,g=G.gs;if(g[g.length-2]===j&&mv)g.pop();else if(!g.includes(j)){g.push(j);pluck(F.e,.08,.25)}guess()}
$("wheel").addEventListener("pointerdown",e=>{const b=e.target.closest(".lt[data-j]");if(!b)return;dn=1;mv=0;hit(b)});
$("wheel").addEventListener("pointermove",e=>{if(!dn)return;const x=document.elementFromPoint(e.clientX,e.clientY),b=x&&x.closest&&x.closest(".lt[data-j]");if(b&&+b.dataset.j!==G.gs[G.gs.length-1]){mv=1;hit(b)}});
addEventListener("pointerup",()=>{if(dn&&G&&G.gs.length){dn=0;send()}dn=0});
function send(){if(!G||!G.gs.length)return;const w=G.gs.map(j=>G.ls[j]).join("");G.gs=[];guess();const p=G.ws.find(q=>q.w===w);
if(p&&!done(p)){p.keys.forEach(k=>{if(!G.rv.has(k))G.nw.push(k);G.rv.add(k)});ok();paint();if(G.ws.every(done))setTimeout(win,500)}
else if(p||G.bws.includes(w))toast("Бул сөз мурда табылган");
else if(G.ex.includes(w)){G.ex=G.ex.filter(x=>x!==w);G.bws.push(w);S.bw++;S.g+=2;save();upd();ok();toast("Бонус сөз! +2 💎 · Ө +1")}
else{bad();const e=$("wheel");e.classList.add("sh");setTimeout(()=>e.classList.remove("sh"),420)}}
function bonus(){modal(`<h3>Бонус сөздөр</h3><p>${G.bws.length?G.bws.join(", "):"Азырынча жок. Башка сөздөрдү да издеңиз!"}</p><button class="mb d" onclick="cm()">Жабуу</button>`)}
function hint(){const u=G.ws.filter(p=>!done(p));if(!u.length)return;if(S.g<10)return toast("Алмаз жетишпейт (10 💎)");S.g-=10;save();upd();
const p=u[Math.random()*u.length|0],r=p.keys.filter(k=>!G.rv.has(k)),k=r[Math.random()*r.length|0];G.rv.add(k);G.nw.push(k);pluck(F.A,.15,.5);paint();if(G.ws.every(done))setTimeout(win,500)}
function win(){const n=G.n,dl=G.dl,r=dl?50:10+Math.min(n,30);S.g+=r;if(dl)S.d=td();else if(n===S.u)S.u++;
if(S.ld!==td()){const y=new Date(Date.now()-864e5).toISOString().slice(0,10);S.s=S.ld===y?S.s+1:1;S.ld=td()}
save();upd();ok();confetti();
modal(`<h3>Азаматсыз!</h3><p>Сиз <b>+${r} 💎</b> таптыңыз!</p><p style="color:#7a5a3a;font-style:italic">${MK[Math.random()*MK.length|0]}</p>${dl?"":`<button class="mb" onclick="cm();play(${S.u})">Кийинки деңгээл</button>`}<button class="mb d" onclick="cm();home()">Меню</button>`)}
/* ---------- бүркүт жана кар барсы ---------- */
let eOn=0,lOn=0;
function fly(){if(eOn)return;eOn=1;const e=$("eg"),W=innerWidth,H=innerHeight,l=Math.random()<.5,y0=H*(.08+Math.random()*.3),y1=H*(.08+Math.random()*.3);e.style.display="block";e.firstChild.style.transform=l?"none":"scaleX(-1)";
const a=e.animate([{transform:`translate(${l?-110:W+20}px,${y0}px)`},{transform:`translate(${l?W+20:-110}px,${y1}px)`}],{duration:5000,easing:"ease-in-out"});a.onfinish=()=>{e.style.display="none";eOn=0}}
function walk(){if(lOn)return;lOn=1;const e=$("lp"),W=innerWidth,l=Math.random()<.5,y=innerHeight-105;e.style.display="block";e.firstChild.style.transform=l?"none":"scaleX(-1)";
const a=e.animate([{transform:`translate(${l?-180:W+20}px,${y}px)`},{transform:`translate(${l?W+20:-180}px,${y}px)`}],{duration:5500,easing:"linear"});a.onfinish=()=>{e.style.display="none";lOn=0}}
function tapFx(ev,n){ev.stopPropagation();const e=ev.currentTarget;S.g+=n;save();upd();ok();toast("+"+n+" 💎");e.getAnimations().forEach(a=>a.finish())}
(function t(){setTimeout(()=>{fly();t()},5000+Math.random()*5000)})();
(function t(){setTimeout(()=>{walk();t()},5000+Math.random()*5000)})();
home();
</script></body></html>
"""

PAGE = HTML.encode("utf-8")


class H(BaseHTTPRequestHandler):
    def out(self, code, ctype, data, head=False, extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if not head:
            self.wfile.write(data)

    def static(self, name, head):
        fp = os.path.join(ST, os.path.basename(name))
        if not os.path.isfile(fp):
            return self.out(404, "text/plain", b"", head)
        size = os.path.getsize(fp)
        a, b, code = 0, size - 1, 200
        m = re.match(r"bytes=(\d*)-(\d*)", self.headers.get("Range", ""))
        if m and (m.group(1) or m.group(2)):
            if m.group(1):
                a = int(m.group(1))
            if m.group(2):
                b = min(int(m.group(2)), size - 1)
            code = 206
        if a > b:
            return self.out(416, "text/plain", b"", head)
        with open(fp, "rb") as f:
            f.seek(a)
            d = f.read(b - a + 1)
        ex = {"Accept-Ranges": "bytes"}
        if code == 206:
            ex["Content-Range"] = "bytes %d-%d/%d" % (a, b, size)
        self.out(code, mimetypes.guess_type(fp)[0] or "application/octet-stream", d, head, ex)

    def go(self, head):
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        if u.path in ("/", "/index.html"):
            return self.out(200, "text/html; charset=utf-8", PAGE, head)
        if u.path.startswith("/f/"):
            return self.static(u.path[3:], head)
        if u.path == "/api/level":
            t = time.time()
            HITS[:] = [x for x in HITS if t - x < 60]
            HITS.append(t)
            try:
                if not KEY or len(HITS) > 40:
                    raise RuntimeError("AI off or rate limit")
                g = lambda k, d="": q.get(k, [d])[0]
                d = ai_level(g("n", "1"), min(max(int(g("len", "5")), 5), 8), g("theme")[:40], g("avoid")[:300])
                return self.out(200, "application/json", json.dumps(d, ensure_ascii=False).encode(), head)
            except Exception as e:
                print("AI error:", repr(e)[:300])
                return self.out(502, "application/json", b"{}", head)
        self.out(404, "text/plain", b"", head)

    def do_GET(self):
        self.go(False)

    def do_HEAD(self):
        self.go(True)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print("Server started on port", PORT, "| AI key set:", bool(KEY))
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
