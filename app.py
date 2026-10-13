<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Блиц-опрос</title>
<style>
:root{box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
*{box-sizing:border-box}html,body{height:100%;margin:0}
body{font-family:system-ui,"Segoe UI",Roboto,sans-serif;background:#0b1d2a;color:#fff;overflow-x:hidden}
#bg{position:fixed;inset:0;z-index:0}#bg svg{width:100%;height:100%;display:block}
#shade{position:fixed;inset:0;z-index:1;background:rgba(5,15,25,.0);transition:.6s}
.on-dim #shade{background:rgba(5,15,25,.62)}
.screen{position:relative;z-index:2;display:none;min-height:100%;padding:16px;flex-direction:column;align-items:center}
.screen.act{display:flex}
#s-start{justify-content:center}
h1{font-size:clamp(32px,7vw,64px);margin:0 0 24px;text-shadow:0 4px 20px #0008;text-align:center}
.btn{border:0;border-radius:999px;padding:14px 34px;font-size:20px;font-weight:700;color:#fff;cursor:pointer;background:linear-gradient(135deg,#ff9a3c,#ff4f7b);box-shadow:0 8px 24px #0006;transition:transform .15s}
.btn:hover{transform:scale(1.06)}.btn.big{font-size:30px;padding:22px 64px;animation:pulse 2s infinite}
.btn.ok{background:linear-gradient(135deg,#22c55e,#15803d)}.btn.no{background:linear-gradient(135deg,#ef4444,#991b1b)}.btn.gray{background:#334155}
@keyframes pulse{50%{box-shadow:0 0 0 18px #ff9a3c22,0 8px 24px #0006}}
.panel{background:#0f2638cc;backdrop-filter:blur(8px);border:1px solid #fff3;border-radius:22px;padding:22px;width:min(640px,100%);margin:auto}
.panel h2{margin:0 0 14px}.lbl{margin:16px 0 8px;font-weight:600;opacity:.85}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{padding:10px 16px;border-radius:12px;background:#ffffff18;border:2px solid transparent;cursor:pointer;font-size:16px;color:#fff}
.chip.sel{background:#ff9a3c;border-color:#fff;font-weight:700}
.names{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px}
.names input{padding:10px;border-radius:10px;border:2px solid;background:#0008;color:#fff;font-size:15px}
#board{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;width:100%;max-width:1000px}
.team{flex:1 1 130px;max-width:190px;text-align:center;padding:10px 8px;border-radius:16px;background:#0f2638dd;border:3px solid var(--c);transition:.3s;position:relative}
.team .n{font-weight:700;font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.team .p{font-size:38px;font-weight:800;color:var(--c)}
.team.glow{animation:glow 1.2s infinite alternate;transform:scale(1.07);background:#17384f}
@keyframes glow{from{box-shadow:0 0 8px var(--c),0 0 16px var(--c)}to{box-shadow:0 0 26px var(--c),0 0 52px var(--c)}}
.team .tag{font-size:12px;opacity:0;height:14px}.team.glow .tag{opacity:1}
#info{margin:12px 0;font-size:18px;opacity:.9;text-align:center}
#grid{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;width:min(640px,100%)}
.cell{aspect-ratio:1.3;border-radius:16px;border:0;font-size:clamp(22px,5vw,36px);font-weight:800;color:#fff;cursor:pointer;background:linear-gradient(135deg,#2dd4bf,#0ea5e9);box-shadow:0 6px 16px #0005;transition:.15s}
.cell:hover:not(:disabled){transform:translateY(-4px) scale(1.05)}
.cell:disabled{background:#1e293b;color:#64748b;cursor:default;box-shadow:none}
.modal{position:fixed;inset:0;z-index:10;background:#000a;display:none;align-items:center;justify-content:center;padding:16px}
.modal.act{display:flex}
.card{background:#10283b;border:2px solid #fff4;border-radius:24px;padding:26px;width:min(720px,100%);text-align:center;animation:pop .3s}
@keyframes pop{from{transform:scale(.8);opacity:0}}
.card .q{font-size:clamp(20px,4vw,30px);margin:16px 0;font-weight:600}
.card .a{font-size:clamp(22px,4vw,32px);color:#4ade80;font-weight:800;margin:14px 0}
.badge{display:inline-block;padding:6px 14px;border-radius:999px;background:#ffffff20;margin:2px}
.special{background:linear-gradient(135deg,#a855f7,#ec4899);font-weight:700}
.row{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-top:12px}
#win{position:fixed;inset:0;z-index:20;display:none;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:16px}
#win.act{display:flex}#win .trophy{font-size:clamp(80px,20vw,160px);animation:bounce 1s infinite alternate}
@keyframes bounce{to{transform:translateY(-20px) rotate(6deg)}}
#win h2{font-size:clamp(28px,6vw,56px);margin:6px 0;text-shadow:0 4px 20px #000}
#win .sc{font-size:28px;margin-bottom:18px}
.fall{position:fixed;top:-60px;z-index:19;pointer-events:none;animation:fall linear forwards}
@keyframes fall{to{transform:translateY(115vh) rotate(540deg)}}
#toast{position:fixed;left:50%;top:18%;transform:translateX(-50%);z-index:30;font-size:34px;font-weight:800;padding:12px 28px;border-radius:20px;background:#000c;display:none}
.fade{opacity:.12;pointer-events:none;transition:1s}
.err{color:#fca5a5;margin-top:10px}
.wheelwrap{position:relative;width:min(300px,80vw);margin:18px auto 8px}.ptr{position:absolute;top:-18px;left:50%;transform:translateX(-50%);font-size:32px;z-index:2;color:#fff;text-shadow:0 2px 6px #000}#wheel svg{width:100%;display:block}
.spinb{margin-top:6px;border:0;border-radius:10px;padding:6px 8px;font-size:12px;font-weight:700;background:var(--c);color:#111;cursor:pointer;width:100%}.spinb:disabled{background:#334155;color:#cbd5e1;cursor:default}
#mute{position:fixed;right:12px;bottom:calc(12px + env(safe-area-inset-bottom,0px));z-index:25;display:none;border:0;border-radius:50%;width:48px;height:48px;font-size:22px;background:#000a;color:#fff;cursor:pointer}
#toast{text-align:center}#toast svg{display:block;margin:0 auto 6px}.trophy svg{display:block}.fall svg{display:block}.mres{font-size:26px;font-weight:800;margin:10px 0}
@media(max-width:480px){#grid{grid-template-columns:repeat(4,1fr)}}
</style></head><body>
<div id="bg"></div><div id="shade"></div>

<div class="screen act" id="s-start">
  <h1>🌿 Блиц-опрос</h1>
  <button class="btn big" id="go">Начать</button>
</div>

<div class="screen" id="s-setup">
  <div class="panel">
    <h2>⚙️ Панель управления</h2>
    <div class="lbl">Класс</div><div class="chips" id="c-grade"></div>
    <div class="lbl">Предмет</div><div class="chips" id="c-subj"></div>
    <div class="lbl">Сколько команд (до 5)</div><div class="chips" id="c-teams"></div>
    <div class="lbl">Названия команд</div><div class="names" id="names"></div>
    <div class="lbl">Сколько вопросов (до 20)</div><div class="chips" id="c-q"></div>
    <div class="row"><button class="btn" id="play">🚀 Запустить игру</button></div>
    <div class="err" id="err"></div>
  </div>
</div>

<div class="screen" id="s-game">
  <div id="board"></div>
  <div id="info"></div>
  <div id="grid"></div>
  <div class="row" style="margin:22px 0"><button class="btn no" id="fin">Завершить игру</button></div>
</div>

<div class="modal" id="m"><div class="card" id="card"></div></div>
<div id="toast"></div>
<button id="mute" title="Музыка">🔊</button>
<div class="modal" id="rm"><div class="card" id="rc"></div></div>
<div id="win"></div>

<script>
const SUBJ=["Математика","Физика","Литература","Кыргызский язык","История мира","История Кыргызстана","Биология","Русский язык"];
const COL=["#ff6b6b","#4dabf7","#51cf66","#fcc419","#cc5de8"];
const $=id=>document.getElementById(id);
let cfg={grade:5,subj:SUBJ[0],teams:2,q:20},G=null,audio=null,sample=null;
const R=(a,b)=>a+Math.random()*(b-a);

/* ---------- случайный пейзаж (SVG) ---------- */
function scene(){
  const P=[["#ffb36b","#ff6f91","#2b1b4d"],["#7ad7ff","#c8f2ff","#1b6b8a"],["#ffd89b","#19547b","#0b3d2e"],["#a1c4fd","#c2e9fb","#2d6a4f"],["#f6d365","#fda085","#3a2c6b"],["#0f2027","#2c5364","#0b3d2e"]];
  const p=P[Math.floor(R(0,P.length))],W=1200,H=700,hz=420;
  let s=`<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid slice"><defs><linearGradient id="sk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${p[0]}"/><stop offset="1" stop-color="${p[1]}"/></linearGradient><linearGradient id="wt" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${p[1]}"/><stop offset="1" stop-color="${p[2]}"/></linearGradient></defs><rect width="${W}" height="${H}" fill="url(#sk)"/>`;
  for(let i=0;i<30;i++)s+=`<circle cx="${R(0,W)}" cy="${R(0,200)}" r="${R(.6,1.6)}" fill="#fff" opacity=".5"/>`;
  s+=`<circle cx="${R(150,1050)}" cy="${R(90,230)}" r="${R(40,70)}" fill="#fff" opacity=".85"/>`;
  for(let i=0;i<3;i++){const cx=R(0,W),cy=R(60,200);s+=`<g fill="#fff" opacity=".5"><ellipse cx="${cx}" cy="${cy}" rx="90" ry="22"/><ellipse cx="${cx+50}" cy="${cy-12}" rx="60" ry="20"/></g>`;}
  const sh=["#fff","#9db4c0","#4f6d7a"];
  for(let l=0;l<3;l++){let d=`M0 ${hz}`;const n=6+l*2;for(let i=0;i<=n;i++)d+=` L${i*W/n} ${hz-R(60,230)+l*50}`;d+=` L${W} ${hz} Z`;s+=`<path d="${d}" fill="${p[2]}" opacity="${.35+l*.25}"/>`;}
  s+=`<rect y="${hz}" width="${W}" height="${H-hz}" fill="url(#wt)"/>`;
  for(let i=0;i<8;i++)s+=`<rect x="${R(0,W)}" y="${R(hz+20,H)}" width="${R(60,200)}" height="3" fill="#fff" opacity=".25"/>`;
  for(let i=0;i<26;i++){const x=R(-20,W+20),h=R(70,190),y=hz+R(-10,60),w=h*.4;s+=`<path d="M${x} ${y} l${w/2} ${-h*.5} h${-w*.25} l${w*.35} ${-h*.4} h${-w*.2} l${w*.3} ${-h*.35} l${-w*.3} ${h*.35} h${-w*.2} l${w*.35} ${h*.4} h${-w*.25} z" fill="#0b3d2e" opacity="${R(.7,1)}"/>`;}
  return s+`<rect y="${H-70}" width="${W}" height="70" fill="${p[2]}" opacity=".7"/></svg>`;
}
$("bg").innerHTML=scene();

/* ---------- экраны ---------- */
function show(id){document.querySelectorAll(".screen").forEach(e=>e.classList.toggle("act",e.id===id));document.body.classList.toggle("on-dim",id!=="s-start");}
$("go").onclick=()=>{show("s-setup");};

function chips(id,items,key,fmt){const el=$(id);el.innerHTML="";items.forEach(v=>{const b=document.createElement("button");b.className="chip"+(cfg[key]===v?" sel":"");b.textContent=fmt?fmt(v):v;b.onclick=()=>{cfg[key]=v;chips(id,items,key,fmt);if(key==="teams")names();};el.appendChild(b);});}
function names(){const el=$("names"),old=[...el.querySelectorAll("input")].map(i=>i.value);el.innerHTML="";for(let i=0;i<cfg.teams;i++){const inp=document.createElement("input");inp.placeholder="Команда "+(i+1);inp.value=old[i]||"";inp.style.borderColor=COL[i];el.appendChild(inp);}}
chips("c-grade",[1,2,3,4,5,6,7,8,9],"grade",v=>v+" класс");
chips("c-subj",SUBJ,"subj");
chips("c-teams",[1,2,3,4,5],"teams");
chips("c-q",[10,15,20],"q");
names();

/* ---------- ИИ: генерация вопросов ---------- */
async function genQuestions(){
  const n=cfg.q;
  const lang=cfg.subj==="Кыргызский язык"?"Вопросы по кыргызскому языку пиши на русском, а примеры слов давай на кыргызском.":"Пиши по-русски.";
  const prompt=`Ты составитель школьных блиц-викторин. Составь ровно ${n} разных вопросов для ${cfg.grade} класса школы Кыргызстана по предмету «${cfg.subj}» по школьной программе. Сложность растёт от лёгких к сложным, но всё по уровню ${cfg.grade} класса. Вопросы короткие, ответ однозначный и короткий (слово, число, фраза). Темы не повторяй. ${lang} Верни ТОЛЬКО JSON-массив вида [{"q":"вопрос","a":"ответ"}], без пояснений и без markdown.`;
  const r=await sample.json(prompt);
  if(!Array.isArray(r)||r.length<n)throw new Error("ИИ вернул неполный список");
  return r.slice(0,n).map(x=>({q:String(x.q),a:String(x.a)}));
}

$("play").onclick=async()=>{
  $("err").textContent="";
  musicInit();const btn=$("play");btn.disabled=true;btn.textContent="⏳ ИИ придумывает вопросы…";
  try{
    sample=sample||await claude.use("sample");
    if(!sample)throw new Error("ИИ недоступен в этом окне");
    const qs=await genQuestions();
    const inputs=[...$("names").querySelectorAll("input")];
    const teams=inputs.map((i,k)=>({name:i.value.trim()||"Команда "+(k+1),score:0}));
    // 2 особые клетки: бонус/штраф от -30 до +30
    const idx=[...Array(qs.length).keys()].sort(()=>Math.random()-.5).slice(0,2);
    const vals=[10,20,30,-10,-20,-30].sort(()=>Math.random()-.5);
    const cells=qs.map((q,i)=>({...q,done:false,sp:idx.includes(i)?vals[idx.indexOf(i)]:0}));
    G={teams,cells,turn:0,cur:-1,left:qs.length,over:false,spin:teams.map(()=>0)};
    renderGame();show("s-game");musicStart();
  }catch(e){$("err").textContent="Ошибка: "+(e.message||e.code||e)+". Попробуйте ещё раз.";}
  btn.disabled=false;btn.textContent="🚀 Запустить игру";
};

/* ---------- игра ---------- */
function renderGame(){
  const b=$("board");b.innerHTML="";
  G.teams.forEach((t,i)=>{const d=document.createElement("div");d.className="team"+(i===G.turn?" glow":"");d.style.setProperty("--c",COL[i]);d.innerHTML='<div class="n"></div><div class="p"></div><div class="tag">▶ отвечает</div><button class="spinb" data-i="'+i+'"></button>';d.querySelector(".n").textContent=t.name;d.querySelector(".spinb").onclick=()=>openRoulette(i);d.querySelector(".p").textContent=t.score;b.appendChild(d);});
  updSpin();$("info").textContent=`${cfg.grade} класс • ${cfg.subj} • отвечает: ${G.teams[G.turn].name}. Выберите номер вопроса`;
  const g=$("grid");g.innerHTML="";
  G.cells.forEach((c,i)=>{const e=document.createElement("button");e.className="cell";e.textContent=c.done?"✓":i+1;e.disabled=c.done;e.onclick=()=>openQ(i);g.appendChild(e);});
}
function openQ(i){
  G.cur=i;const c=G.cells[i],t=G.teams[G.turn];
  const card=$("card");
  card.innerHTML=`<span class="badge" style="border:2px solid ${COL[G.turn]}"></span><span class="badge">Вопрос №${i+1}</span>${c.sp>0?'<span class="badge special">🎁 Бонус-вопрос: +'+c.sp+'</span>':''}${c.sp<0?'<span class="badge special">⚠️ Рискованный вопрос: при ошибке '+c.sp+'</span>':''}<div class="q"></div><div id="ans"></div><div class="row" id="acts"></div>`;
  card.querySelector(".badge").textContent=t.name;
  card.querySelector(".q").textContent=c.q;
  const sb=document.createElement("button");sb.className="btn gray";sb.textContent="👁 Показать ответ";
  sb.onclick=()=>{$("ans").innerHTML='<div class="a"></div>';$("ans").firstChild.textContent=c.a;$("acts").innerHTML="";
    const y=document.createElement("button");y.className="btn ok";y.textContent="✅ Верно";y.onclick=()=>resolve(true);
    const n=document.createElement("button");n.className="btn no";n.textContent="❌ Неверно";n.onclick=()=>resolve(false);
    $("acts").append(y,n);};
  $("acts").appendChild(sb);$("m").classList.add("act");
}
function toast(t,k){const e=$("toast");e.innerHTML=meme(k,null,130)+'<div></div>';e.lastChild.textContent=t;e.style.display="block";setTimeout(()=>e.style.display="none",1600);}
function resolve(ok){
  const c=G.cells[G.cur],t=G.teams[G.turn];let d=0;
  if(ok)d=c.sp>0?c.sp:15;else if(c.sp<0)d=c.sp;
  t.score+=d;c.done=true;G.left--;
  $("m").classList.remove("act");
  toast(d>0?"+"+d:""+d,d>0?"win":d<0?"cry":"derp");
  if(G.left===0){setTimeout(win,1400);renderGame();return;}
  G.turn=(G.turn+1)%G.teams.length;renderGame();
}

/* ---------- мемы (рисуются кодом) ---------- */
const MEMES={
 cool:{bg:"#4dabf7",f:"#ffd43b",c:["ИЗИ","ГЕНИЙ","ЛЕГЕНДА"],x:'<rect x="28" y="38" width="20" height="11" rx="3" fill="#111"/><rect x="52" y="38" width="20" height="11" rx="3" fill="#111"/><rect x="47" y="41" width="6" height="3" fill="#111"/><path d="M36 59Q50 71 64 59" stroke="#111" stroke-width="3" fill="none"/>'},
 win:{bg:"#51cf66",f:"#ffd43b",c:["УРА!","МОЛОДЦЫ","КРАСАВЧИКИ"],x:'<path d="M30 42Q36 34 42 42M58 42Q64 34 70 42" stroke="#111" stroke-width="3" fill="none"/><path d="M34 56Q50 76 66 56Z" fill="#7f1d1d" stroke="#111" stroke-width="2"/><path d="M36 14L50 -4L64 14Z" fill="#ec4899" transform="translate(0 6)"/>'},
 cry:{bg:"#868e96",f:"#ffd43b",c:["НЕ ТАК!","БОЛЬНО","ЭЭЭЭ"],x:'<path d="M30 42Q36 36 42 42M58 42Q64 36 70 42" stroke="#111" stroke-width="3" fill="none"/><ellipse cx="36" cy="54" rx="3" ry="6" fill="#38bdf8"/><ellipse cx="64" cy="54" rx="3" ry="6" fill="#38bdf8"/><path d="M38 66Q50 56 62 66" stroke="#111" stroke-width="3" fill="none"/>'},
 shock:{bg:"#cc5de8",f:"#ffd43b",c:["ВАУ!","ЧТО?!"],x:'<circle cx="38" cy="42" r="8" fill="#fff" stroke="#111" stroke-width="2"/><circle cx="62" cy="42" r="8" fill="#fff" stroke="#111" stroke-width="2"/><circle cx="38" cy="42" r="3" fill="#111"/><circle cx="62" cy="42" r="3" fill="#111"/><ellipse cx="50" cy="64" rx="6" ry="8" fill="#111"/>'},
 derp:{bg:"#fcc419",f:"#ffe066",c:["ЭМММ","ХМ...","ОПС"],x:'<circle cx="38" cy="42" r="9" fill="#fff" stroke="#111" stroke-width="2"/><circle cx="63" cy="44" r="5" fill="#fff" stroke="#111" stroke-width="2"/><circle cx="41" cy="44" r="3" fill="#111"/><circle cx="64" cy="45" r="2" fill="#111"/><path d="M36 62H64" stroke="#111" stroke-width="3"/><path d="M52 62V72Q57 76 62 72V62Z" fill="#f472b6"/>'},
 smug:{bg:"#ff922b",f:"#ffd43b",c:["Я ЗНАЛ","ЛЕГКО"],x:'<circle cx="38" cy="44" r="6" fill="#fff" stroke="#111" stroke-width="2"/><circle cx="62" cy="44" r="6" fill="#fff" stroke="#111" stroke-width="2"/><circle cx="40" cy="45" r="2.5" fill="#111"/><circle cx="64" cy="45" r="2.5" fill="#111"/><path d="M30 40H46M56 36L70 40" stroke="#111" stroke-width="4"/><path d="M38 62Q56 68 66 56" stroke="#111" stroke-width="3" fill="none"/>'},
 angry:{bg:"#ff6b6b",f:"#ff8787",c:["ГРРР","КТО ТАК?!"],x:'<path d="M28 34L46 42M72 34L54 42" stroke="#111" stroke-width="4"/><circle cx="38" cy="48" r="3" fill="#111"/><circle cx="62" cy="48" r="3" fill="#111"/><path d="M36 68Q50 56 64 68" stroke="#111" stroke-width="3" fill="none"/>'}
};
function meme(k,cap,size){const m=MEMES[k]||MEMES.derp;cap=cap||m.c[Math.floor(Math.random()*m.c.length)];size=size||120;
 return `<svg width="${size}" height="${size}" viewBox="0 0 100 100"><rect width="100" height="100" rx="10" fill="${m.bg}"/><circle cx="50" cy="46" r="30" fill="${m.f}" stroke="#111" stroke-width="2"/>${m.x}<text x="50" y="94" text-anchor="middle" font-size="14" font-weight="900" font-family="Impact,'Arial Black',sans-serif" fill="#fff" stroke="#000" stroke-width="3" paint-order="stroke">${cap}</text></svg>`;}

/* ---------- веселая музыка (без слов) ---------- */
let mus=null;
const mtof=m=>440*Math.pow(2,(m-69)/12);
const MEL=[[72,0,76,79,76,0,74,72],[69,0,72,76,72,0,71,69],[72,0,77,81,77,0,76,72],[74,0,79,83,79,0,77,74]],ROOT=[48,45,41,43];
function musicInit(){try{if(mus)return;const ac=new (window.AudioContext||window.webkitAudioContext)();const g=ac.createGain();g.gain.value=.5;g.connect(ac.destination);const nb=ac.createBuffer(1,ac.sampleRate*.05,ac.sampleRate),d=nb.getChannelData(0);for(let i=0;i<d.length;i++)d[i]=Math.random()*2-1;mus={ac,g,nb,muted:false,step:0,t:0,iv:null};ac.resume();}catch(e){mus=null;}}
function tone(f,t,dur,type,v){const ac=mus.ac,o=ac.createOscillator(),g=ac.createGain();o.type=type;o.frequency.value=f;g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(v,t+.02);g.gain.exponentialRampToValueAtTime(.0001,t+dur);o.connect(g).connect(mus.g);o.start(t);o.stop(t+dur+.05);}
function beat(s,t){const bar=Math.floor(s/8)%4,i=s%8,m=MEL[bar][i];
 if(m)tone(mtof(m),t,.22,"square",.05);
 if(i%2===0)tone(mtof(ROOT[bar]+(i%4===2?7:0)),t,.28,"triangle",.22);
 if(i===0||i===4){const o=mus.ac.createOscillator(),g=mus.ac.createGain();o.frequency.setValueAtTime(140,t);o.frequency.exponentialRampToValueAtTime(40,t+.15);g.gain.setValueAtTime(.35,t);g.gain.exponentialRampToValueAtTime(.001,t+.18);o.connect(g).connect(mus.g);o.start(t);o.stop(t+.2);}
 if(i%2===1){const n=mus.ac.createBufferSource(),g=mus.ac.createGain(),f=mus.ac.createBiquadFilter();n.buffer=mus.nb;f.type="highpass";f.frequency.value=7000;g.gain.value=.08;n.connect(f).connect(g).connect(mus.g);n.start(t);}}
function musicStart(){if(!mus)return;mus.ac.resume();clearInterval(mus.iv);mus.step=0;mus.t=mus.ac.currentTime+.1;const dt=60/136/2;mus.iv=setInterval(()=>{while(mus.t<mus.ac.currentTime+.3){beat(mus.step,mus.t);mus.t+=dt;mus.step++;}},100);$("mute").style.display="block";}
function stopMusic(){if(!mus)return;clearInterval(mus.iv);$("mute").style.display="none";}
$("mute").onclick=()=>{if(!mus)return;mus.muted=!mus.muted;mus.g.gain.value=mus.muted?0:.5;$("mute").textContent=mus.muted?"🔇":"🔊";};
$("fin").onclick=()=>win();

/* ---------- рулетка ---------- */
const SEG=[30,0,-30,30,0,-30],CD=180000;
function fmt(ms){const s=Math.ceil(ms/1000);return Math.floor(s/60)+":"+String(s%60).padStart(2,"0");}
function updSpin(){if(!G)return;document.querySelectorAll(".spinb").forEach(b=>{const left=CD-(Date.now()-G.spin[+b.dataset.i]);b.disabled=left>0;b.textContent=left>0?"⏳ "+fmt(left):"🎡 Рулетка";});}
setInterval(updSpin,1000);
function wheelSvg(){let s='<svg viewBox="-100 -100 200 200"><circle r="98" fill="#fff"/>';const col=v=>v>0?"#22c55e":v<0?"#ef4444":"#64748b";
 for(let k=0;k<6;k++){const a0=k*60*Math.PI/180,a1=(k+1)*60*Math.PI/180,P=(a,r)=>(r*Math.sin(a)).toFixed(1)+" "+(-r*Math.cos(a)).toFixed(1);
  const v=SEG[k];s+=`<path d="M0 0L${P(a0,92)}A92 92 0 0 1 ${P(a1,92)}Z" fill="${col(v)}" stroke="#fff" stroke-width="2"/><text transform="rotate(${k*60+30})" y="-60" text-anchor="middle" font-size="${v?22:16}" font-weight="800" fill="#fff">${v>0?"+30":v<0?"-30":"пусто"}</text>`;}
 return s+'<circle r="9" fill="#111"/></svg>';}
function openRoulette(i){
 if(!G||G.over||Date.now()-G.spin[i]<CD)return;
 const rc=$("rc");rc.innerHTML='<h2></h2><div class="wheelwrap"><div class="ptr">▼</div><div id="wheel">'+wheelSvg()+'</div></div><div class="mres" id="rres"></div><div class="row"><button class="btn" id="spinGo">Крутить!</button><button class="btn gray" id="spinX">Закрыть</button></div>';
 rc.querySelector("h2").textContent="Рулетка: "+G.teams[i].name;
 $("rm").classList.add("act");
 $("spinX").onclick=()=>$("rm").classList.remove("act");
 $("spinGo").onclick=()=>{
  $("spinGo").style.display="none";$("spinX").style.display="none";G.spin[i]=Date.now();
  const k=Math.floor(Math.random()*6),w=$("wheel");
  w.style.transition="transform 4s cubic-bezier(.12,.7,.1,1)";w.style.transform=`rotate(${360*6+360-(k*60+30)}deg)`;
  setTimeout(()=>{if(G.over)return;const v=SEG[k];G.teams[i].score+=v;
   $("rres").innerHTML=meme(v>0?"win":v<0?"cry":"derp",null,110)+'<div></div>';$("rres").lastChild.textContent=v>0?"+30 баллов!":v<0?"-30 баллов":"Пусто";
   $("spinX").style.display="";renderGame();},4200);};
}

/* ---------- победа ---------- */
function win(){if(!G||G.over)return;G.over=true;$("m").classList.remove("act");$("rm").classList.remove("act");
  const max=Math.max(...G.teams.map(t=>t.score)),w=G.teams.filter(t=>t.score===max);
  $("s-game").classList.add("fade");
  const el=$("win");
  el.innerHTML='<div class="trophy">'+meme("cool","ЧЕМПИОНЫ",230)+'</div><h2></h2><div class="sc"></div><button class="btn" id="again">🔄 Новая игра</button>';
  el.querySelector("h2").textContent=(w.length>1?"Победили: ":"Победитель: ")+w.map(t=>t.name).join(" и ");
  el.querySelector(".sc").textContent=max+" баллов!";
  el.classList.add("act");$("again").onclick=()=>{el.classList.remove("act");$("s-game").classList.remove("fade");stopAudio();$("bg").innerHTML=scene();show("s-start");};
  stopMusic();confetti();fanfare();
}
function confetti(){
  const S=Object.keys(MEMES);
  let n=0;const iv=setInterval(()=>{for(let k=0;k<4;k++){const e=document.createElement("div");e.className="fall";e.innerHTML=meme(S[Math.floor(R(0,S.length))],null,R(80,140));e.style.left=R(0,90)+"vw";e.style.animationDuration=R(3,6)+"s";document.body.appendChild(e);setTimeout(()=>e.remove(),6500);}if(++n>60)clearInterval(iv);},120);
}
function fanfare(){
  try{
    const ac=audio=new (window.AudioContext||window.webkitAudioContext)();
    const notes=[523,659,784,1047,784,1047,1319,1047,1319,1568];
    notes.forEach((f,i)=>{const t=ac.currentTime+i*.18;[f,f/2].forEach((fr,j)=>{const o=ac.createOscillator(),g=ac.createGain();o.type=j?"triangle":"square";o.frequency.value=fr;g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(j?.12:.07,t+.03);g.gain.exponentialRampToValueAtTime(.0001,t+(i>=notes.length-1?1.4:.22));o.connect(g).connect(ac.destination);o.start(t);o.stop(t+1.5);});});
  }catch(e){}
}
function stopAudio(){try{audio&&audio.close();}catch(e){}}
</script></body></html>
