// ─── Dashboard Formatters & Icons ───
const IC={
  bot:'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="10" x="3" y="11" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/></svg>',
  book:'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>',
  cal:'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
  money:'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="12" x="2" y="6" rx="2"/><circle cx="12" cy="12" r="2"/><path d="M6 12h.01M18 12h.01"/></svg>',
  msg:'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
  cog:'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
  play:'<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="5 3 19 12 5 21 5 3"/></svg>',
  chev:'<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>',
  check:'<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
};

// ── TOUR ──────────────────────────────────────────────────────────
const TSTEPS=[
  {ib:'#fef3c7',ic:'#d97706',sv:IC.play,  t:'ยินดีต้อนรับสู่ OrgChat AI',   b:'ระบบจัดการองค์กรอัจฉริยะ รวม AI แชท, คลังความรู้, ปฏิทิน, รายจ่าย และอีกมากมายไว้ในที่เดียว', el:null},
  {ib:'#ede9fe',ic:'#7c3aed',sv:IC.cog,   t:'เมนูหลัก',                    b:'แถบเมนูด้านซ้ายรวบรวมทุกฟีเจอร์ครบ กดที่รายการใดก็ได้เพื่อสลับส่วนงาน บนมือถือกด ☰ มุมบนขวา', el:'#navSidebar'},
  {ib:'#dbeafe',ic:'#2563eb',sv:IC.bot,   t:'แชทกับ AI',                   b:'พิมพ์ถามอะไรก็ได้ทั้งภาษาไทยและอังกฤษ AI ตอบโดยอ้างอิงจากเอกสารใน Knowledge Base ขององค์กร', el:'#nav-chat'},
  {ib:'#ecfdf5',ic:'#059669',sv:IC.book,  t:'คลังความรู้ (KB)',             b:'อัปโหลด PDF, Word, Excel หรือรูปภาพ ให้ AI ตอบจากข้อมูลขององค์กรได้แม่นยำขึ้น', el:'#nav-kb'},
  {ib:'#fef9c3',ic:'#ca8a04',sv:IC.cal,   t:'ปฏิทินและการลา',              b:'บันทึกนัดหมาย วันหยุด คำขอลาของทีม ระบบแจ้งเตือนอัตโนมัติผ่าน LINE', el:'#nav-calendar'},
  {ib:'#dcfce7',ic:'#16a34a',sv:IC.money, t:'รายจ่าย & Dashboard',          b:'บันทึกค่าใช้จ่ายองค์กร ดูกราฟ Dashboard สรุปยอดรายเดือน แยกตามหมวดหมู่', el:'#nav-dashboard'},
  {ib:'#f1f5f9',ic:'#475569',sv:IC.cog,   t:'จัดการแพลน',                  b:'ดูการใช้งานเทียบกับ Limit อัปเกรด หรือยกเลิกแพลนได้จากเมนู จัดการแพลน', el:'a[href="/plan"]'},
  {ib:'#dcfce7',ic:'#16a34a',sv:IC.check, t:'พร้อมใช้งานแล้ว',             b:'รู้จักฟีเจอร์หลักครบแล้ว กดปุ่ม ? มุมขวาล่าง (หรือ Shift+?) เพื่อเปิดศูนย์ช่วยเหลือได้ตลอดเวลา', el:null},
];
let _ti=0,_ta=false;

function startTour(){closeHelp();_ti=0;_ta=true;document.getElementById('tourOverlay').style.display='block';_ts();}
function endTour(){_ta=false;['tourOverlay','tourSpot','tourCard'].forEach(id=>document.getElementById(id).style.display='none');localStorage.setItem('orgchat_tour_done','1');}
function tourGo(d){_ti+=d;if(_ti<0)_ti=0;if(_ti>=TSTEPS.length){endTour();return;}_ts();}

function _ts(){
  const s=TSTEPS[_ti],card=document.getElementById('tourCard'),spot=document.getElementById('tourSpot');
  document.getElementById('tStep').textContent=(_ti+1)+' / '+TSTEPS.length;
  document.getElementById('tTitle').textContent=s.t;
  document.getElementById('tBody').textContent=s.b;
  document.getElementById('tPrev').style.display=_ti===0?'none':'';
  document.getElementById('tNext').textContent=_ti===TSTEPS.length-1?'เสร็จสิ้น':'ถัดไป →';
  const iw=document.getElementById('tIconWrap');
  iw.style.background=s.ib;iw.innerHTML='<span style="color:'+s.ic+'">'+s.sv+'</span>';
  document.getElementById('tDots').innerHTML=TSTEPS.map((_,i)=>'<div style="width:'+(i===_ti?'20px':'6px')+';height:6px;border-radius:9999px;background:'+(i===_ti?'#0f172a':'#e2e8f0')+';transition:all .3s"></div>').join('');

  if(!s.el){
    spot.style.display='none';
    card.style.cssText='display:block;position:fixed;z-index:9002;width:320px;background:#fff;border-radius:16px;padding:20px;box-shadow:0 20px 60px rgba(0,0,0,.28);font-family:Sarabun,Outfit,sans-serif;top:50%;left:50%;transform:translate(-50%,-50%);visibility:visible;';
    return;
  }
  const el=document.querySelector(s.el);
  if(!el){spot.style.display='none';card.style.cssText='display:block;position:fixed;z-index:9002;width:320px;background:#fff;border-radius:16px;padding:20px;box-shadow:0 20px 60px rgba(0,0,0,.28);font-family:Sarabun,Outfit,sans-serif;top:50%;left:50%;transform:translate(-50%,-50%);visibility:visible;';return;}

  // Instant scroll then position
  el.scrollIntoView({block:'nearest',inline:'nearest',behavior:'instant'});
  card.style.visibility='hidden';card.style.display='block';card.style.transform='';
  card.style.width='300px';card.style.left='-9999px';card.style.top='-9999px';

  requestAnimationFrame(()=>requestAnimationFrame(()=>{
    const r=el.getBoundingClientRect(),cw=card.offsetWidth||300,ch=card.offsetHeight||260;
    const pad=7,mg=12,vw=window.innerWidth,vh=window.innerHeight;
    spot.style.cssText='display:block;position:fixed;z-index:9001;pointer-events:none;border-radius:10px;box-shadow:0 0 0 9999px rgba(0,0,0,.7),0 0 0 3px #34d399,0 0 0 6px rgba(52,211,153,.25);transition:top .25s,left .25s,width .25s,height .25s;left:'+(r.left-pad)+'px;top:'+(r.top-pad)+'px;width:'+(r.width+pad*2)+'px;height:'+(r.height+pad*2)+'px;';
    let cx,cy;
    if(r.right+cw+20+mg<=vw)cx=r.right+20;
    else if(r.left-cw-20-mg>=0)cx=r.left-cw-20;
    else cx=Math.max(mg,Math.min(vw/2-cw/2,vw-cw-mg));
    cy=r.top+r.height/2-ch/2;
    if(cx<r.right+4&&cx+cw>r.left-4)cy=(vh-r.bottom-mg>=ch+16)?r.bottom+16:r.top-ch-16;
    cx=Math.max(mg,Math.min(cx,vw-cw-mg));cy=Math.max(mg,Math.min(cy,vh-ch-mg));
    card.style.left=cx+'px';card.style.top=cy+'px';card.style.visibility='visible';
  }));
}

window.addEventListener('keydown',e=>{if(e.key==='Escape'&&_ta)endTour();});
window.addEventListener('resize',()=>{if(_ta)_ts();});

// ── HELP CENTER ───────────────────────────────────────────────────
const HCATS=[
  {id:'ai',  lbl:'AI แชท',         ico:IC.bot,  items:[
    {q:'วิธีถามตอบกับ AI น้องพั้นซ์', a:'พิมพ์คำถามลงในช่องข้อความเพื่อเริ่มสนทนา น้องพั้นซ์จะตอบคำถามโดยประมวลผลร่วมกับเอกสาร นโยบาย และข้อมูลองค์กรที่คุณอัปโหลดไว้ให้อัตโนมัติค่ะ<br><button onclick="closeHelp();showView(\'chat\')" class="inline-flex items-center gap-1 px-3 py-1.5 bg-slate-900 text-white text-[11px] font-bold rounded-lg hover:bg-slate-800 transition mt-2 cursor-pointer">👉 เปิดหน้า AI แชทตอนนี้</button>'},
    {q:'AI ตอบข้อมูลโดยอ้างอิงจากที่ไหนบ้าง', a:'น้องพั้นซ์จะตอบคำถามโดยอ้างอิงจาก 2 แหล่งข้อมูลหลัก:<br>1. <strong>ความรู้ทั่วไปของโมเดล (Base LLM):</strong> ใช้ตอบงานทั่วไป แปลภาษา หรือคำนวณสูตร<br>2. <strong>คลังข้อมูลองค์กร (Knowledge Base):</strong> เอกสาร PDF, Word, Excel หรือรูปภาพที่คุณอัปโหลดไว้ เพื่อให้ได้คำตอบที่ถูกต้องและเจาะจงตามระเบียบบริษัทของคุณค่ะ'},
    {q:'ช่วยสรุปและวิเคราะห์เอกสารได้ไหม', a:'<strong>ทำได้แน่นอนค่ะ!</strong> คุณสามารถพิมพ์สั่ง เช่น <em>"ช่วยสรุปไฟล์คู่มือพนักงานให้หน่อย"</em> หรือ <em>"วิเคราะห์ยอดรายจ่ายจากตารางนี้ให้ที"</em> ระบบจะประมวลผลเนื้อหาและแจกแจงเป็นข้อๆ สรุปตัวเลขสำคัญให้ทันทีค่ะ'},
    {q:'การเข้าใช้งาน AI ส่งผลต่อโควตาอย่างไร', a:'ทุกการถามตอบกับ AI จะถูกนับจำนวนโควตาตามข้อกำหนดของแพลนที่องค์กรเลือกใช้ สามารถตรวจสอบจำนวนโควตาที่ใช้ไปและโควตาคงเหลือประจำเดือนได้ที่หน้าจัดการแพลนค่ะ<br><button onclick="closeHelp();showView(\'plan\')" class="inline-flex items-center gap-1 px-3 py-1.5 bg-slate-900 text-white text-[11px] font-bold rounded-lg hover:bg-slate-800 transition mt-2 cursor-pointer">👉 ตรวจสอบโควตาใช้งาน</button>'},
  ]},
  {id:'kb',  lbl:'คลังความรู้ KB', ico:IC.book, items:[
    {q:'ขั้นตอนการอัปโหลดเอกสารเข้าระบบ', a:'1. เข้าไปที่เมนู <strong>คลังความรู้ KB</strong><br>2. คลิกปุ่ม <strong>+ อัปโหลดไฟล์</strong> ที่มุมบนขวา<br>3. เลือกไฟล์เอกสารที่ต้องการ ระบบจะทำการประมวลผลข้อความและบันทึกเข้าสู่สมองของ AI ทันทีค่ะ<br><button onclick="closeHelp();showView(\'kb\')" class="inline-flex items-center gap-1 px-3 py-1.5 bg-slate-900 text-white text-[11px] font-bold rounded-lg hover:bg-slate-800 transition mt-2 cursor-pointer">👉 เปิดหน้าคลังความรู้ KB</button>'},
    {q:'รูปแบบไฟล์และขนาดสูงสุดที่ระบบรองรับ', a:'ระบบรองรับไฟล์หลากหลายประเภทดังนี้:<br>• <strong>เอกสารพิมพ์:</strong> PDF, DOCX (Word), XLSX (Excel), CSV, TXT<br>• <strong>รูปภาพและสแกน:</strong> PNG, JPG, JPEG, WEBP<br>• <strong>ขนาดไฟล์สูงสุด:</strong> ไม่เกิน 20 MB ต่อไฟล์ค่ะ'},
    {q:'วิธีจัดการ ลบ หรืออัปเดตเอกสารเก่า', a:'เมื่อต้องการแก้ไขหรืออัปเดตข้อมูลเอกสาร ให้คุณลบไฟล์เวอร์ชันเก่าออกก่อนโดยเข้าไปที่หน้าคลังความรู้ KB คลิกที่ปุ่ม <strong>ลบ (ถังขยะ)</strong> บนไฟล์นั้นๆ จากนั้นอัปโหลดไฟล์ตัวใหม่เข้าไปแทนที่ เพื่อไม่ให้ AI นำข้อมูลเก่ามาสับสนกับข้อมูลใหม่ค่ะ'},
  ]},
  {id:'cal', lbl:'ปฏิทินการลา',    ico:IC.cal,  items:[
    {q:'การสร้างและบันทึกกิจกรรมองค์กร', a:'คุณสามารถสร้างนัดหมายหรือกิจกรรมสำคัญได้ง่ายๆ โดยคลิกที่วันที่บนปฏิทิน หรือกดปุ่ม <strong>+ เพิ่มกำหนดการ</strong> เพื่อเพิ่มข้อมูลนัดหมาย ซึ่งสามารถแชร์เป็นสาธารณะเพื่อให้ทุกคนเห็น หรือส่งแจ้งเตือนเข้าแชท LINE กลุ่มได้ค่ะ<br><button onclick="closeHelp();showView(\'calendar\')" class="inline-flex items-center gap-1 px-3 py-1.5 bg-slate-900 text-white text-[11px] font-bold rounded-lg hover:bg-slate-800 transition mt-2 cursor-pointer">👉 เปิดปฏิทินองค์กร</button>'},
    {q:'ขั้นตอนการยื่นใบลาหยุดสำหรับพนักงาน', a:'1. ไปที่เมนู <strong>การลา</strong><br>2. คลิกปุ่ม <strong>+ ขอลาหยุด</strong><br>3. เลือกประเภทการลา (ลาป่วย/ลากิจ/ลาพักร้อน) พร้อมระบุช่วงวันที่ เหตุผล และผู้จัดการที่พิจารณา<br>4. ระบบจะทำการยิงแจ้งเตือนใบขอลาไปยังแอดมินหรือผู้จัดการทันทีค่ะ<br><button onclick="closeHelp();showView(\'leave\')" class="inline-flex items-center gap-1 px-3 py-1.5 bg-slate-900 text-white text-[11px] font-bold rounded-lg hover:bg-slate-800 transition mt-2 cursor-pointer">👉 ยื่นใบลาหยุดตอนนี้</button>'},
    {q:'การพิจารณาและอนุมัติใบลาของแอดมิน', a:'สำหรับแอดมินหรือหัวหน้างาน สามารถตรวจสอบคำขอลาคงค้างของพนักงานได้ในเมนู <strong>การลา</strong> โดยระบบจะมีปุ่มให้คลิก <strong>อนุมัติ (✓)</strong> หรือ <strong>ปฏิเสธ (✕)</strong> พร้อมช่องให้ใส่เหตุผลประกอบ ซึ่งระบบจะตอบกลับผลการอนุมัติไปยังผู้ขอลาทางหน้าเว็บและ LINE อัตโนมัติค่ะ'},
  ]},
  {id:'fin', lbl:'รายจ่ายการเงิน',  ico:IC.money,items:[
    {q:'การบันทึกรายจ่ายและสแกนสลิปด้วย AI', a:'1. เข้าสู่เมนู <strong>รายจ่าย & Dashboard</strong><br>2. คลิกปุ่ม <strong>+ เพิ่มรายการรายจ่าย</strong> หรือลากรูปภาพใบเสร็จ/สลิปโอนเงินมาวาง<br>3. AI OCR จะทำการสแกนหายอดเงิน วันที่ และชื่อร้านค้าคู่ค้าเพื่อกรอกฟอร์มให้คุณโดยอัตโนมัติ ช่วยลดความผิดพลาดในการคีย์มือค่ะ<br><button onclick="closeHelp();showView(\'dashboard\')" class="inline-flex items-center gap-1 px-3 py-1.5 bg-slate-900 text-white text-[11px] font-bold rounded-lg hover:bg-slate-800 transition mt-2 cursor-pointer">👉 บันทึกรายจ่าย & แดชบอร์ด</button>'},
    {q:'การบันทึกหัก ณ ที่จ่าย (WHT)', a:'เมื่อทำการเพิ่มรายจ่ายประเภทการจ้างงานหรือจ้างบริการ คุณสามารถเปิดสวิตช์ <strong>มีหัก ณ ที่จ่าย</strong> เพื่อเลือกระบุอัตราภาษีหัก ณ ที่จ่าย เช่น 1% (ขนส่ง), 3% (บริการ/จ้างทำของ), 5% (ค่าเช่า) โดยระบบจะบันทึกและคำนวณมูลค่าภาษีสะสมเพื่อออกเอกสารนำส่งให้ทันทีค่ะ'},
    {q:'การส่งออกรายงานบัญชีและรายงานภาษี', a:'สำหรับผู้ใช้งานแพลนระดับ Ultra ขึ้นไป สามารถคลิกปุ่ม <strong>Export</strong> ที่หัวมุมบนขวาในหน้าแดชบอร์ดรายจ่าย เพื่อรวบรวมข้อมูลค่าใช้จ่าย ภาษีซื้อ (VAT) และรายการหัก ณ ที่จ่ายดาวน์โหลดเป็นไฟล์ Excel หรือ PDF เพื่อส่งต่อให้สำนักงานบัญชีได้ในคลิกเดียวค่ะ'},
  ]},
  {id:'line',lbl:'LINE Bot',         ico:IC.msg,  items:[
    {q:'ขั้นตอนการเชื่อมโยงระบบเข้ากับ LINE Bot', a:'1. ไปที่เมนู <strong>การตั้งค่า</strong> เลื่อนลงมาที่หมวดหมู่ <strong>LINE Bot Settings</strong><br>2. สแกน QR Code หรือแอดไลน์ไอดีบอทประจำองค์กร<br>3. หากต้องการใช้ในกลุ่มไลน์ของบริษัท ให้ทำการดึงบอทเข้ากลุ่มแล้วพิมพ์สั่งงานได้ทันทีค่ะ<br><button onclick="closeHelp();showView(\'settings\')" class="inline-flex items-center gap-1 px-3 py-1.5 bg-slate-900 text-white text-[11px] font-bold rounded-lg hover:bg-slate-800 transition mt-2 cursor-pointer">👉 ไปที่หน้าตั้งค่าเชื่อมต่อ</button>'},
    {q:'LINE Bot รองรับคำสั่งอะไรบ้าง', a:'• <strong>ถามข้อมูลคลังความรู้:</strong> พิมพ์สอบถามระเบียบหรือข้อมูลบริษัท บอทจะใช้ AI ค้นหาเอกสารมาตอบทันทีค่ะ<br>• <strong>สแกนบันทึกรายจ่าย:</strong> เพียงถ่ายรูปสลิปโอนเงินหรือใบเสร็จส่งเข้าแชท บอทจะถอดข้อมูลบันทึกเข้าฐานข้อมูลอัตโนมัติ<br>• <strong>แจ้งเตือนองค์กร:</strong> แจ้งเตือนการขอลาหยุด วันหยุด หรือนัดหมายสำคัญของบริษัทเข้าแชทโดยตรง'},
    {q:'กรณี LINE Bot ไม่ตอบกลับหรือใช้งานไม่ได้', a:'กรุณาเข้าไปตรวจสอบความถูกต้องของค่า <code>LINE_CHANNEL_SECRET</code> และ <code>LINE_CHANNEL_ACCESS_TOKEN</code> ที่ป้อนไว้ในหน้าตั้งค่า และตรวจสอบสถานะบอทว่าเปิดใช้งานอยู่ (Active) หรือไม่ค่ะ'},
  ]},
  {id:'acc', lbl:'บัญชีและแพลน',    ico:IC.cog,  items:[
    {q:'การเชิญพนักงานและกำหนดสิทธิ์ผู้ใช้', a:'แอดมินองค์กรสามารถเชิญพนักงานเข้ามามีส่วนร่วมในระบบได้โดยไปที่เมนู <strong>จัดการองค์กร</strong> กรอกอีเมลหรือสร้างลิงก์เชิญส่งต่อให้พนักงาน และสามารถเลือกกำหนดบทบาทเป็น แอดมิน (Admin) หรือ สมาชิก (Member) ได้ค่ะ<br><button onclick="closeHelp();showView(\'org\')" class="inline-flex items-center gap-1 px-3 py-1.5 bg-slate-900 text-white text-[11px] font-bold rounded-lg hover:bg-slate-800 transition mt-2 cursor-pointer">👉 จัดการพนักงานในองค์กร</button>'},
    {q:'การอัปเกรด จัดการ หรือยกเลิกแผนใช้งาน', a:'คุณสามารถเปรียบเทียบสิทธิ์แต่ละแพลนและตรวจสอบสถิติการใช้งานจริง (จำนวนไฟล์ KB, สมาชิก, AI Query) ได้ที่เมนู <strong>จัดการแพลน</strong> หากต้องการอัปเกรดหรือยกเลิก สามารถทำธุรกรรมและจัดการรายละเอียดผ่าน Stripe Secure Portal ได้ทันทีค่ะ<br><button onclick="closeHelp();showView(\'plan\')" class="inline-flex items-center gap-1 px-3 py-1.5 bg-slate-900 text-white text-[11px] font-bold rounded-lg hover:bg-slate-800 transition mt-2 cursor-pointer">👉 ไปที่หน้าจัดการแพลน</button>'},
    {q:'วิธีกู้คืนหรือเปลี่ยนรหัสผ่าน', a:'• <strong>เปลี่ยนรหัสผ่าน:</strong> ทำได้ที่เมนู <strong>การตั้งค่า > ความปลอดภัย</strong><br>• <strong>กรณีลืมรหัสผ่าน:</strong> กดปุ่ม "ลืมรหัสผ่าน" ที่หน้าเข้าสู่ระบบ กรอกอีเมลของบัญชีเพื่อรับลิงก์รีเซตรหัสผ่านผ่านอีเมลค่ะ'},
  ]},
];
let _hc='ai';

function _initHelpModal() {
  const m = document.getElementById('helpModal');
  if (m && !m._hasHelpListener) {
    m._hasHelpListener = true;
    m.addEventListener('click', e => { if (e.target === m) closeHelp(); });
  }
}
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', _initHelpModal);
} else {
  _initHelpModal();
}

function openHelp(){
  _initHelpModal();
  const m = document.getElementById('helpModal');
  if (m) m.style.display = 'flex';
  const s = document.getElementById('helpSearch');
  if (s) s.value = '';
  _hn();
  _hb(_hc);
}
function closeHelp(){
  const m = document.getElementById('helpModal');
  if (m) m.style.display = 'none';
}

function _hn(){
  document.getElementById('helpNav').innerHTML=
    HCATS.map(c=>'<button class="hnav-item'+(c.id===_hc?' active':'')+'" onclick="_hw(\''+c.id+'\')"><div class="hni">'+c.ico+'</div><span>'+c.lbl+'</span></button>').join('')+
    '<div style="border-top:1px solid #f1f5f9;margin:8px 4px"></div><button class="hnav-item" onclick="closeHelp();startTour()"><div class="hni" style="background:#fef3c7">'+IC.play+'</div><span style="color:#92400e">เริ่ม Tour</span></button>';
}
function _hw(id){_hc=id;document.getElementById('helpSearch').value='';_hn();_hb(id);}
function _hb(id){
  const c=HCATS.find(x=>x.id===id);if(!c)return;
  document.getElementById('helpBody').innerHTML=
    '<div style="display:flex;align-items:center;gap:9px;margin-bottom:14px;padding-bottom:12px;border-bottom:1px solid #f1f5f9"><div style="width:30px;height:30px;border-radius:7px;background:#f1f5f9;display:flex;align-items:center;justify-content:center">'+c.ico+'</div><span style="font-size:14px;font-weight:800;color:#0f172a">'+c.lbl+'</span><span style="font-size:11px;color:#94a3b8;margin-left:auto">'+c.items.length+' บทความ</span></div>'+
    c.items.map((it,i)=>_fq(id+i,it.q,it.a)).join('')+
    '<div style="margin-top:14px;padding:13px 15px;background:#f8fafc;border:1px solid #f1f5f9;border-radius:10px;display:flex;align-items:center;gap:10px"><div style="flex:1"><div style="font-size:12.5px;font-weight:700;color:#0f172a">ยังหาคำตอบไม่ได้?</div><div style="font-size:11.5px;color:#64748b;margin-top:1px">ติดต่อทีมงานได้โดยตรง</div></div><a href="mailto:mxmm2547@gmail.com" style="background:#0f172a;color:#fff;border-radius:8px;padding:7px 13px;font-size:12px;font-weight:700;text-decoration:none;white-space:nowrap">ติดต่อเรา</a></div>';
}
function _fq(id,q,a){return '<div class="hfaq"><div class="hfaq-q" onclick="_ft(\''+id+'\')"><span>'+q+'</span><span class="hfaq-ch" id="hch'+id+'">'+IC.chev+'</span></div><div class="hfaq-a" id="hfa'+id+'">'+a+'</div></div>';}
function _ft(id){const a=document.getElementById('hfa'+id),c=document.getElementById('hch'+id);const o=a.style.display==='block';a.style.display=o?'none':'block';c.style.transform=o?'':'rotate(180deg)';}

function filterHelp(q){
  const v=q.trim().toLowerCase();if(!v){_hb(_hc);return;}
  const res=[];HCATS.forEach(c=>c.items.forEach(it=>{if(it.q.toLowerCase().includes(v)||it.a.toLowerCase().includes(v))res.push({lbl:c.lbl,ico:c.ico,...it});}));
  const body=document.getElementById('helpBody');
  if(!res.length){body.innerHTML='<div style="text-align:center;padding:3rem 1rem"><svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg><p style="font-size:13px;color:#94a3b8;margin-top:10px">ไม่พบผลลัพธ์สำหรับ <strong style="color:#64748b">'+q+'</strong></p></div>';return;}
  body.innerHTML='<p style="font-size:11px;color:#94a3b8;margin-bottom:10px">พบ '+res.length+' ผลลัพธ์</p>'+res.map((it,i)=>'<div style="margin-bottom:4px"><div style="font-size:10px;color:#94a3b8;font-weight:700;margin-bottom:2px;display:flex;align-items:center;gap:4px"><span style="display:inline-flex">'+it.ico+'</span>'+it.lbl+'</div>'+_fq('sr'+i,it.q,it.a)+'</div>').join('');
}

window.addEventListener('keydown',e=>{if(e.shiftKey&&e.key==='?'&&!_ta){const m=document.getElementById('helpModal');if(m)m.style.display==='flex'?closeHelp():openHelp();}});

// ─── Financial Dashboard & Reports UI ───
/* ─── helpers ─── */
const _api = (url, opts={}) => fetch(url, {headers:{'Content-Type':'application/json'}, credentials:'same-origin', ...opts});
const _json = (url, opts={}) => _api(url, opts).then(r=>r.json());
function _fmt(n){ return Number(n||0).toLocaleString('th-TH', {minimumFractionDigits:2, maximumFractionDigits:2}); }
function _fmtDate(s){ return s ? s.substring(0,10) : '—'; }

/* ════════════════════════════════════════════════
   QUOTATION / INVOICE
   ════════════════════════════════════════════════ */
let _qtList = [];
const STAGE_COLORS = {
  draft: 'bg-surface-100 text-surface-600 dark:bg-surface-800 dark:text-surface-300 border-surface-200 dark:border-surface-700',
  sent: 'bg-sky-50 text-sky-700 dark:bg-sky-950/40 dark:text-sky-300 border-sky-200 dark:border-sky-800/60',
  approved: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800/60',
  paid: 'bg-teal-50 text-teal-700 dark:bg-teal-950/40 dark:text-teal-300 border-teal-200 dark:border-teal-800/60',
  rejected: 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300 border-rose-200 dark:border-rose-800/60'
};
const STAGE_TH = { draft: 'ร่าง', sent: 'ส่งแล้ว', approved: 'อนุมัติ', paid: 'ชำระแล้ว', rejected: 'ปฏิเสธ' };

function updateQtKpiStats() {
  const totalCount = _qtList.length;
  const totalVal = _qtList.reduce((acc, x) => acc + Math.max(0, Number(x.total || 0)), 0);
  const draftCount = _qtList.filter(x => x.status === 'draft').length;
  const sentCount = _qtList.filter(x => x.status === 'sent').length;
  const paidCount = _qtList.filter(x => x.status === 'approved' || x.status === 'paid').length;

  const countEl = document.getElementById('kpi-qt-total-count');
  const valEl = document.getElementById('kpi-qt-total-val');
  const draftEl = document.getElementById('kpi-qt-draft-count');
  const sentEl = document.getElementById('kpi-qt-sent-count');
  const paidEl = document.getElementById('kpi-qt-paid-count');

  if (countEl) countEl.textContent = totalCount;
  if (valEl) valEl.textContent = '฿' + _fmt(totalVal);
  if (draftEl) draftEl.textContent = draftCount;
  if (sentEl) sentEl.textContent = sentCount;
  if (paidEl) paidEl.textContent = paidCount;
}

function switchQtTab(tab) {
  const dashPanel = document.getElementById('qt-dashboard-panel');
  const creatorPanel = document.getElementById('qt-creator-panel');
  const tabDash = document.getElementById('tab-qt-dashboard');
  const tabCreator = document.getElementById('tab-qt-creator');
  const pdfBtn = document.getElementById('generatePdfBtn');

  if (tab === 'creator') {
    if (dashPanel) dashPanel.classList.add('hidden');
    if (creatorPanel) creatorPanel.classList.remove('hidden');
    if (tabDash) {
      tabDash.className = 'px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all text-surface-500 hover:text-surface-900 dark:hover:text-white flex items-center gap-1.5 cursor-pointer';
    }
    if (tabCreator) {
      tabCreator.className = 'px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all bg-white dark:bg-surface-700 text-brand-600 dark:text-white shadow-xs flex items-center gap-1.5 cursor-pointer';
    }
    if (pdfBtn) pdfBtn.classList.remove('hidden');
    if (typeof initDocumentGenerator === 'function') initDocumentGenerator();
  } else {
    if (creatorPanel) creatorPanel.classList.add('hidden');
    if (dashPanel) dashPanel.classList.remove('hidden');
    if (tabDash) {
      tabDash.className = 'px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all bg-white dark:bg-surface-700 text-brand-600 dark:text-white shadow-xs flex items-center gap-1.5 cursor-pointer';
    }
    if (tabCreator) {
      tabCreator.className = 'px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all text-surface-500 hover:text-surface-900 dark:hover:text-white flex items-center gap-1.5 cursor-pointer';
    }
    if (pdfBtn) pdfBtn.classList.add('hidden');
    loadQuotations();
  }
  if (typeof lucide !== 'undefined') lucide.createIcons();
}

async function changeQuotationStatus(id, status) {
  try {
    const res = await _json(`/api/quotations/${id}/status`, {
      method: 'POST',
      body: JSON.stringify({ status })
    });
    if (res.ok) {
      toast('อัปเดตสถานะสำเร็จ', 'success');
      loadQuotations();
    } else {
      toast(res.error || 'ไม่สามารถอัปเดตสถานะได้', 'error');
    }
  } catch (err) {
    toast('เกิดข้อผิดพลาดในการเปลี่ยนสถานะ', 'error');
  }
}

async function loadQuotations() {
  const type = document.getElementById('qt-type-f')?.value || '';
  const status = document.getElementById('qt-status-f')?.value || '';
  let url = '/api/quotations';
  const params = [];
  if (type) params.push(`type=${type}`);
  if (status) params.push(`status=${status}`);
  if (params.length) url += '?' + params.join('&');
  const d = await _json(url);
  _qtList = d.quotations || [];
  renderQuotations();
}

function renderQuotations() {
  const el = document.getElementById('quotation-list');
  if (!el) return;
  const q = (document.getElementById('qt-search')?.value || '').toLowerCase().trim();
  const typeF = document.getElementById('qt-type-f')?.value || '';
  const statusF = document.getElementById('qt-status-f')?.value || '';

  const list = _qtList.filter(x => {
    if (typeF && x.type !== typeF) return false;
    if (statusF && x.status !== statusF) return false;
    if (q) {
      const matchNo = x.quotation_no?.toLowerCase().includes(q);
      const matchCust = x.customer_name?.toLowerCase().includes(q);
      const matchCompany = x.customer_company?.toLowerCase().includes(q);
      if (!matchNo && !matchCust && !matchCompany) return false;
    }
    return true;
  });

  updateQtKpiStats();

  if (!list.length) {
    el.innerHTML = `
      <div class="col-span-full py-20 text-center">
        <div class="w-16 h-16 rounded-3xl bg-surface-100 dark:bg-surface-800 text-surface-400 flex items-center justify-center mx-auto mb-4 shadow-inner">
          <i data-lucide="file-question" class="w-8 h-8 opacity-40"></i>
        </div>
        <h4 class="text-sm font-bold text-surface-700 dark:text-surface-300 mb-1">ยังไม่มีเอกสารในหมวดหมู่นี้</h4>
        <p class="text-xs text-surface-400 max-w-sm mx-auto mb-5">เริ่มต้นสร้างใบเสนอราคาหรือใบแจ้งหนี้เพื่อส่งให้ลูกค้าและพิมพ์ PDF ได้ทันที</p>
        <button onclick="_showQtModal()" class="inline-flex items-center gap-1.5 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold rounded-xl shadow-md shadow-brand-500/20 transition-all hover:scale-102 cursor-pointer">
          <i data-lucide="plus-circle" class="w-4 h-4"></i>
          <span>สร้างเอกสารแรก</span>
        </button>
      </div>`;
    if (typeof lucide !== 'undefined') lucide.createIcons();
    return;
  }

  const STAGE_META = {
    draft: { label: 'ร่างเอกสาร', badge: 'bg-surface-100 text-surface-600 dark:bg-surface-800 dark:text-surface-300 border-surface-200 dark:border-surface-700', dot: 'bg-surface-400' },
    sent: { label: 'ส่งแล้ว', badge: 'bg-sky-50 text-sky-700 dark:bg-sky-950/40 dark:text-sky-300 border-sky-200 dark:border-sky-800/60', dot: 'bg-sky-500' },
    approved: { label: 'อนุมัติแล้ว', badge: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800/60', dot: 'bg-emerald-500' },
    paid: { label: 'ชำระเงินแล้ว', badge: 'bg-teal-50 text-teal-700 dark:bg-teal-950/40 dark:text-teal-300 border-teal-200 dark:border-teal-800/60', dot: 'bg-teal-500' },
    rejected: { label: 'ปฏิเสธ', badge: 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300 border-rose-200 dark:border-rose-800/60', dot: 'bg-rose-500' }
  };

  el.innerHTML = list.map(q => {
    const isInvoice = q.type === 'invoice';
    const st = STAGE_META[q.status] || { label: q.status, badge: 'bg-surface-100 text-surface-500', dot: 'bg-surface-400' };
    const itemsCount = Array.isArray(q.items) ? q.items.length : 0;
    const totalVal = Math.max(0, Number(q.total || 0));

    return `
    <div class="bg-white dark:bg-surface-900 rounded-3xl border border-surface-200/80 dark:border-surface-800 p-6 shadow-xs hover:shadow-xl hover:border-brand-300 dark:hover:border-brand-700/60 transition-all duration-200 flex flex-col justify-between group relative overflow-hidden">
      <!-- Top Accent Line -->
      <div class="absolute top-0 left-0 right-0 h-1.5 ${isInvoice ? 'bg-gradient-to-r from-amber-500 to-orange-500' : 'bg-gradient-to-r from-brand-500 to-indigo-500'} opacity-80 group-hover:opacity-100 transition-opacity"></div>

      <div>
        <!-- Card Header: Type, Document No, Status Badge -->
        <div class="flex items-start justify-between gap-2 mb-4">
          <div class="min-w-0">
            <div class="flex items-center gap-1.5 mb-1">
              <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${isInvoice ? 'bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-800/40' : 'bg-brand-50 dark:bg-brand-900/40 text-brand-600 dark:text-brand-400 border border-brand-200 dark:border-brand-800/40'}">
                <i data-lucide="${isInvoice ? 'receipt' : 'file-signature'}" class="w-3 h-3"></i>
                ${isInvoice ? 'INVOICE' : 'QUOTATION'}
              </span>
            </div>
            <h3 class="font-black text-surface-900 dark:text-white text-base tracking-tight font-mono">${q.quotation_no || ('QT-' + q.id)}</h3>
          </div>

          <!-- Status Pill -->
          <div class="flex-shrink-0">
            <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold border ${st.badge} shadow-2xs">
              <span class="w-1.5 h-1.5 rounded-full ${st.dot}"></span>
              ${st.label}
            </span>
          </div>
        </div>

        <!-- Customer Info -->
        <div class="space-y-2 mb-5">
          <div class="flex items-center gap-2 text-surface-800 dark:text-surface-200 font-bold text-xs truncate">
            <i data-lucide="building-2" class="w-4 h-4 text-surface-400 flex-shrink-0"></i>
            <span class="truncate" title="${q.customer_name || 'ไม่ระบุลูกค้า'}">${q.customer_name || 'ไม่ระบุลูกค้า'}</span>
          </div>
          ${q.customer_company ? `
          <div class="flex items-center gap-2 text-surface-400 text-[11px] truncate pl-6">
            <span class="truncate">${q.customer_company}</span>
          </div>` : ''}
          <div class="flex items-center justify-between text-[11px] text-surface-400 pt-2 border-t border-surface-100 dark:border-surface-800/60">
            <span class="flex items-center gap-1"><i data-lucide="package" class="w-3.5 h-3.5"></i> ${itemsCount} รายการ</span>
            <span class="flex items-center gap-1"><i data-lucide="calendar" class="w-3.5 h-3.5"></i> ${_fmtDate(q.created_at)}</span>
          </div>
        </div>
      </div>

      <!-- Card Footer: Total Amount & Action Buttons -->
      <div class="pt-4 border-t border-surface-100 dark:border-surface-800 flex items-center justify-between gap-2">
        <div>
          <span class="text-[10px] font-bold uppercase tracking-wider text-surface-400 block">ยอดสุทธิ</span>
          <span class="font-black text-lg text-emerald-600 dark:text-emerald-400 tabular-nums">฿${_fmt(totalVal)}</span>
        </div>

        <div class="flex items-center gap-1.5">
          <!-- Change Status Quick Menu -->
          <div class="relative">
            <select onchange="changeQuotationStatus(${q.id}, this.value)" title="เปลี่ยนสถานะ" class="text-[10px] font-bold py-1.5 px-2 rounded-xl bg-surface-100 dark:bg-surface-800 text-surface-600 dark:text-surface-300 border border-surface-200 dark:border-surface-700 hover:border-brand-500 cursor-pointer focus:outline-none">
              <option value="draft" ${q.status==='draft'?'selected':''}>ร่าง</option>
              <option value="sent" ${q.status==='sent'?'selected':''}>ส่งแล้ว</option>
              <option value="approved" ${q.status==='approved'?'selected':''}>อนุมัติ</option>
              <option value="paid" ${q.status==='paid'?'selected':''}>ชำระแล้ว</option>
              <option value="rejected" ${q.status==='rejected'?'selected':''}>ปฏิเสธ</option>
            </select>
          </div>

          <!-- Download PDF -->
          <button onclick="downloadQtPdf(${q.id})" class="p-2 bg-surface-100 dark:bg-surface-800 hover:bg-brand-50 dark:hover:bg-brand-900/30 text-surface-500 hover:text-brand-600 dark:hover:text-brand-400 rounded-xl transition-all shadow-2xs cursor-pointer" title="ดาวน์โหลด PDF">
            <i data-lucide="file-down" class="w-4 h-4"></i>
          </button>

          <!-- Edit Button -->
          <button onclick="openQuotationModal(${q.id})" class="p-2 bg-surface-100 dark:bg-surface-800 hover:bg-amber-50 dark:hover:bg-amber-900/30 text-surface-500 hover:text-amber-600 dark:hover:text-amber-400 rounded-xl transition-all shadow-2xs cursor-pointer" title="แก้ไขเอกสาร">
            <i data-lucide="pencil" class="w-4 h-4"></i>
          </button>

          <!-- Delete Button -->
          <button onclick="deleteQuotation(${q.id})" class="p-2 bg-surface-100 dark:bg-surface-800 hover:bg-rose-50 dark:hover:bg-rose-900/30 text-surface-500 hover:text-rose-600 dark:hover:text-rose-400 rounded-xl transition-all shadow-2xs cursor-pointer" title="ลบเอกสาร">
            <i data-lucide="trash-2" class="w-4 h-4"></i>
          </button>
        </div>
      </div>
    </div>`;
  }).join('');

  if (typeof lucide !== 'undefined') lucide.createIcons();
}

async function downloadQtPdf(id) {
  try {
    toast('กำลังสร้างและดาวน์โหลดเอกสาร PDF...', 'info');
    const resp = await fetch(`/api/quotations/${id}/pdf`, {credentials:'same-origin'});
    if (!resp.ok) {
      let errMsg = 'สร้าง PDF ไม่สำเร็จ';
      try {
        const errJson = await resp.json();
        if (errJson && errJson.error) errMsg = errJson.error;
      } catch(e) {}
      toast(errMsg, 'error');
      return;
    }
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `quotation_${id}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast('ดาวน์โหลดเอกสารสำเร็จแล้ว', 'success');
  } catch (err) {
    toast('เกิดข้อผิดพลาดในการดาวน์โหลด: ' + err.message, 'error');
  }
}

async function deleteQuotation(id) {
  if (!confirm('ลบรายการนี้?')) return;
  await _json(`/api/quotations/${id}`, {method:'DELETE'});
  loadQuotations();
}

// Quotation item management
let _qtItems = [];
function qtAddItem() {
  _qtItems.push({name:'',qty:1,unit:'ชิ้น',price:0});
  renderQtItems();
}
function qtRemoveItem(i) { _qtItems.splice(i,1); renderQtItems(); }
function renderQtItems() {
  const el = document.getElementById('qt-items');
  if (!el) return;
  el.innerHTML = _qtItems.map((it,i)=>`
    <div class="flex gap-2 items-center">
      <input type="text" value="${it.name}" onchange="_qtItems[${i}].name=this.value;qtCalc()" placeholder="รายการ" class="flex-1 px-2 py-1.5 text-xs border border-surface-200 dark:border-surface-700 rounded-lg bg-white dark:bg-surface-800 text-surface-900 dark:text-white">
      <input type="number" value="${it.qty}" onchange="_qtItems[${i}].qty=+this.value;qtCalc()" min="1" class="w-16 px-2 py-1.5 text-xs border border-surface-200 dark:border-surface-700 rounded-lg bg-white dark:bg-surface-800 text-surface-900 dark:text-white" placeholder="จำนวน">
      <input type="text" value="${it.unit}" onchange="_qtItems[${i}].unit=this.value" placeholder="หน่วย" class="w-16 px-2 py-1.5 text-xs border border-surface-200 dark:border-surface-700 rounded-lg bg-white dark:bg-surface-800 text-surface-900 dark:text-white">
      <input type="number" value="${it.price}" onchange="_qtItems[${i}].price=+this.value;qtCalc()" min="0" class="w-24 px-2 py-1.5 text-xs border border-surface-200 dark:border-surface-700 rounded-lg bg-white dark:bg-surface-800 text-surface-900 dark:text-white" placeholder="ราคา/หน่วย">
      <span class="w-24 text-xs font-bold text-emerald-600 text-right">${_fmt(it.qty*it.price)}</span>
      <button onclick="qtRemoveItem(${i})" class="text-red-400 hover:text-red-600"><svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>
    </div>`).join('');
  qtCalc();
}
function qtCalc() {
  const subtotal = _qtItems.reduce((s,it)=>s+(it.qty*it.price),0);
  const discount = Math.max(0, parseFloat(document.getElementById('qt-discount')?.value||0));
  const vatRate  = Math.max(0, parseFloat(document.getElementById('qt-vat')?.value||7));
  const whtRate  = Math.max(0, parseFloat(document.getElementById('qt-wht')?.value||0));
  const base = Math.max(0, subtotal - discount);
  const vatAmt = base * vatRate / 100;
  const whtAmt = base * whtRate / 100;
  const total  = Math.max(0, base + vatAmt - whtAmt);
  if (document.getElementById('qt-subtotal')) document.getElementById('qt-subtotal').textContent = _fmt(subtotal);
  if (document.getElementById('qt-vat-amt')) document.getElementById('qt-vat-amt').textContent = _fmt(vatAmt);
  if (document.getElementById('qt-wht-amt')) document.getElementById('qt-wht-amt').textContent = _fmt(whtAmt);
  if (document.getElementById('qt-total')) document.getElementById('qt-total').textContent = _fmt(total);
}

function openQuotationModal(id=null) {
  _qtItems = id ? [] : [{name:'',qty:1,unit:'ชิ้น',price:0}];
  const modal = document.getElementById('qtModal');
  if (!modal) { _showQtModal(id); return; }
  modal.classList.remove('hidden');
}

function _showQtModal(editId=null) {
  const html = `
  <div id="qtModal" class="fixed inset-0 z-[9999] bg-black/60 backdrop-blur-md flex items-center justify-center p-4" onclick="if(event.target===this)closeQtModal()">
    <div class="bg-white dark:bg-surface-900 w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-3xl shadow-2xl">
      <div class="p-6 border-b border-surface-200 dark:border-surface-800 flex items-center justify-between">
        <h3 class="text-lg font-black text-surface-900 dark:text-white">${editId?'แก้ไข':'สร้าง'} ใบเสนอราคา / Invoice</h3>
        <button onclick="closeQtModal()" class="text-surface-400 hover:text-surface-600 p-1"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>
      </div>
      <div class="p-6 space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div><label class="text-xs font-bold text-surface-500 block mb-1">ประเภทเอกสาร</label>
            <select id="qt-type" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white">
              <option value="quotation">ใบเสนอราคา</option><option value="invoice">ใบแจ้งหนี้ / Invoice</option>
            </select></div>
          <div><label class="text-xs font-bold text-surface-500 block mb-1">สถานะ</label>
            <select id="qt-status" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white">
              <option value="draft">ร่าง</option><option value="sent">ส่งแล้ว</option><option value="approved">อนุมัติ</option><option value="rejected">ปฏิเสธ</option><option value="paid">ชำระแล้ว</option>
            </select></div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div><label class="text-xs font-bold text-surface-500 block mb-1">ชื่อลูกค้า *</label>
            <input id="qt-cname" type="text" placeholder="ชื่อ-นามสกุล / บริษัท" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white"></div>
          <div><label class="text-xs font-bold text-surface-500 block mb-1">เลขประจำตัวผู้เสียภาษี</label>
            <input id="qt-ctax" type="text" placeholder="0000000000000" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white"></div>
        </div>
        <div><label class="text-xs font-bold text-surface-500 block mb-1">ที่อยู่ลูกค้า</label>
          <textarea id="qt-caddr" rows="2" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white resize-none"></textarea></div>
        <div class="grid grid-cols-2 gap-4">
          <div><label class="text-xs font-bold text-surface-500 block mb-1">อีเมล</label>
            <input id="qt-cemail" type="email" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white"></div>
          <div><label class="text-xs font-bold text-surface-500 block mb-1">วันหมดอายุ</label>
            <input id="qt-valid" type="date" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white"></div>
        </div>

        <div class="border-t border-surface-200 dark:border-surface-800 pt-4">
          <div class="flex items-center justify-between mb-3">
            <label class="text-xs font-black text-surface-500 uppercase tracking-wider">รายการสินค้า/บริการ</label>
            <button onclick="qtAddItem()" class="text-xs font-bold text-orange-600 hover:underline">+ เพิ่มรายการ</button>
          </div>
          <div id="qt-items" class="space-y-2"></div>
        </div>

        <div class="grid grid-cols-3 gap-3 border-t border-surface-200 dark:border-surface-800 pt-4">
          <div><label class="text-xs font-bold text-surface-500 block mb-1">ส่วนลด (บาท)</label>
            <input id="qt-discount" type="number" value="0" min="0" onchange="qtCalc()" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white"></div>
          <div><label class="text-xs font-bold text-surface-500 block mb-1">VAT %</label>
            <input id="qt-vat" type="number" value="7" min="0" max="20" onchange="qtCalc()" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white"></div>
          <div><label class="text-xs font-bold text-surface-500 block mb-1">WHT %</label>
            <input id="qt-wht" type="number" value="0" min="0" max="15" onchange="qtCalc()" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white"></div>
        </div>

        <div class="bg-surface-50 dark:bg-surface-800 rounded-2xl p-4 space-y-1.5">
          <div class="flex justify-between text-sm"><span class="text-surface-500">ยอดรวมก่อนภาษี</span><span id="qt-subtotal" class="font-bold">0.00</span></div>
          <div class="flex justify-between text-sm"><span class="text-surface-500">VAT</span><span id="qt-vat-amt" class="font-bold">0.00</span></div>
          <div class="flex justify-between text-sm"><span class="text-surface-500">WHT</span><span id="qt-wht-amt" class="font-bold text-red-500">0.00</span></div>
          <div class="flex justify-between font-black text-base border-t border-surface-200 dark:border-surface-700 pt-2 mt-2"><span>ยอดสุทธิ</span><span id="qt-total" class="text-emerald-600">0.00</span></div>
        </div>

        <div><label class="text-xs font-bold text-surface-500 block mb-1">หมายเหตุ</label>
          <textarea id="qt-notes" rows="2" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white resize-none"></textarea></div>
      </div>
      <div class="p-6 border-t border-surface-200 dark:border-surface-800 flex gap-3 justify-end">
        <button onclick="closeQtModal()" class="px-4 py-2 text-sm font-bold text-surface-500 hover:bg-surface-100 dark:hover:bg-surface-800 rounded-xl transition">ยกเลิก</button>
        <button onclick="saveQuotation(${editId||'null'})" class="px-6 py-2 bg-orange-600 hover:bg-orange-700 text-white text-sm font-bold rounded-xl transition">บันทึก</button>
      </div>
    </div>
  </div>`;
  const div = document.createElement('div');
  div.id = 'qtModalWrapper';
  div.innerHTML = html;
  document.body.appendChild(div);
  renderQtItems();
}

function closeQtModal() { document.getElementById('qtModalWrapper')?.remove(); }

async function saveQuotation(editId) {
  const cname = document.getElementById('qt-cname')?.value?.trim();
  if (!cname) { alert('กรุณากรอกชื่อลูกค้า'); return; }
  const subtotal = _qtItems.reduce((s,it)=>s+(it.qty*it.price),0);
  const discount = parseFloat(document.getElementById('qt-discount')?.value||0);
  const vatRate  = parseFloat(document.getElementById('qt-vat')?.value||7);
  const whtRate  = parseFloat(document.getElementById('qt-wht')?.value||0);
  const base = subtotal - discount;
  const vatAmt = base * vatRate / 100;
  const whtAmt = base * whtRate / 100;
  const total  = base + vatAmt - whtAmt;
  const payload = {
    type: document.getElementById('qt-type')?.value,
    status: document.getElementById('qt-status')?.value,
    customer_name: cname,
    customer_tax_id: document.getElementById('qt-ctax')?.value||'',
    customer_address: document.getElementById('qt-caddr')?.value||'',
    customer_email: document.getElementById('qt-cemail')?.value||'',
    valid_until: document.getElementById('qt-valid')?.value||'',
    notes: document.getElementById('qt-notes')?.value||'',
    items: _qtItems, subtotal, discount, vat_rate: vatRate, vat_amount: vatAmt,
    wht_rate: whtRate, wht_amount: whtAmt, total,
  };
  let r;
  if (editId) {
    r = await _json(`/api/quotations/${editId}`, {method:'PUT', body:JSON.stringify(payload)});
  } else {
    r = await _json('/api/quotations', {method:'POST', body:JSON.stringify(payload)});
  }
  if (r.ok) { closeQtModal(); loadQuotations(); toast('บันทึกสำเร็จ','success'); }
  else toast(r.error||'Error','error');
}

/* Quotation view init */
const _origShowView = typeof showView !== 'undefined' ? showView : null;
document.addEventListener('DOMContentLoaded', () => {
  // patch showView to load data on tab switch
  const _sv = window.showView;
  window.showView = function(view, ...args) {
    _sv && _sv(view, ...args);
    if (view === 'quotation') initQuotationView();
    if (view === 'crm') { loadCrmCustomers(); loadCrmDeals(); }
    if (view === 'wht') initWhtView();
    if (view === 'meetings') loadMeetings();
  };
});

function initQuotationView() {
  const el = document.getElementById('view-quotation');
  if (!el) return;
  switchQtTab('dashboard');
  loadQuotations();
  if (typeof lucide !== 'undefined') lucide.createIcons();
}

/* ════════════════════════════════════════════════
   CRM
   ════════════════════════════════════════════════ */
let _crmCustomers=[], _crmDeals=[], _crmDealFilter='';
const DEAL_STAGES = {lead:'Lead',qualified:'Qualified',proposal:'Proposal',negotiation:'Negotiation',won:'Won ✓',lost:'Lost ✗'};
const DEAL_COLORS = {lead:'bg-blue-100 text-blue-700',qualified:'bg-purple-100 text-purple-700',proposal:'bg-yellow-100 text-yellow-700',negotiation:'bg-orange-100 text-orange-700',won:'bg-green-100 text-green-700',lost:'bg-red-100 text-red-700'};

function crmShowTab(tab) {
  document.getElementById('crm-customers-panel').classList.toggle('hidden', tab!=='customers');
  document.getElementById('crm-deals-panel').classList.toggle('hidden', tab!=='deals');
  document.getElementById('crm-tab-customers').className = `btn-xs px-3 py-1.5 rounded-lg text-xs font-bold ${tab==='customers'?'bg-violet-600 text-white':'bg-surface-100 dark:bg-surface-800 text-surface-600 dark:text-surface-300'}`;
  document.getElementById('crm-tab-deals').className = `btn-xs px-3 py-1.5 rounded-lg text-xs font-bold ${tab==='deals'?'bg-violet-600 text-white':'bg-surface-100 dark:bg-surface-800 text-surface-600 dark:text-surface-300'}`;
}

async function loadCrmCustomers() {
  const q = document.getElementById('crm-search')?.value||'';
  const d = await _json(`/api/crm/customers${q?'?q='+encodeURIComponent(q):''}`);
  _crmCustomers = d.customers||[];
  renderCrmCustomers();
}

function renderCrmCustomers() {
  const el = document.getElementById('crm-customers-list');
  if (!el) return;
  if (!_crmCustomers.length) {
    el.innerHTML='<div class="col-span-full py-16 text-center text-surface-400 text-sm">ยังไม่มีลูกค้า</div>'; return;
  }
  el.innerHTML=_crmCustomers.map(c=>`
    <div class="bg-white dark:bg-surface-900 rounded-2xl border border-surface-200 dark:border-surface-800 p-5 hover:shadow-lg transition-all cursor-pointer" onclick="openCrmCustomerDetail(${c.id})">
      <div class="flex items-start gap-3">
        <div class="w-10 h-10 rounded-xl bg-violet-100 dark:bg-violet-900/30 text-violet-600 flex items-center justify-center font-black text-sm flex-shrink-0">${(c.name||'?')[0].toUpperCase()}</div>
        <div class="min-w-0 flex-1">
          <h3 class="font-black text-sm text-surface-900 dark:text-white truncate">${c.name}</h3>
          <p class="text-xs text-surface-400 truncate">${c.company||''}</p>
          ${c.phone?`<p class="text-xs text-surface-400">${c.phone}</p>`:''}
        </div>
      </div>
      <div class="flex gap-2 mt-3 pt-3 border-t border-surface-100 dark:border-surface-800">
        <button onclick="event.stopPropagation();openCrmCustomerModal(${c.id})" class="flex-1 text-center text-xs font-bold text-violet-600 hover:bg-violet-50 dark:hover:bg-violet-900/20 rounded-lg py-1 transition">แก้ไข</button>
        <button onclick="event.stopPropagation();deleteCrmCustomer(${c.id})" class="flex-1 text-center text-xs font-bold text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg py-1 transition">ลบ</button>
      </div>
    </div>`).join('');
}

async function crmSearchCustomers() { loadCrmCustomers(); }

async function openCrmCustomerDetail(cid) {
  const d = await _json(`/api/crm/customers/${cid}`);
  const c = d.customer; const deals = d.deals||[]; const acts = d.activities||[];
  const html = `
  <div class="fixed inset-0 z-[9999] bg-black/60 backdrop-blur-md flex items-center justify-center p-4" id="crmDetailModal" onclick="if(event.target.id==='crmDetailModal')this.remove()">
    <div class="bg-white dark:bg-surface-900 w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-3xl shadow-2xl">
      <div class="p-6 border-b border-surface-200 dark:border-surface-800 flex items-center gap-4">
        <div class="w-14 h-14 rounded-2xl bg-violet-100 dark:bg-violet-900/30 text-violet-600 flex items-center justify-center font-black text-xl">${(c.name||'?')[0].toUpperCase()}</div>
        <div><h3 class="text-lg font-black text-surface-900 dark:text-white">${c.name}</h3>
          <p class="text-sm text-surface-400">${c.company||''} ${c.email?'· '+c.email:''} ${c.phone?'· '+c.phone:''}</p></div>
        <button onclick="document.getElementById('crmDetailModal').remove()" class="ml-auto text-surface-400 hover:text-surface-600"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>
      </div>
      <div class="p-6 space-y-4">
        <div><h4 class="text-xs font-black text-surface-500 uppercase tracking-wider mb-2">Deals (${deals.length})</h4>
          ${deals.map(d=>`<div class="flex items-center gap-3 p-3 bg-surface-50 dark:bg-surface-800 rounded-xl mb-2">
            <span class="text-xs font-bold px-2 py-0.5 rounded-lg ${DEAL_COLORS[d.stage]||''}">${DEAL_STAGES[d.stage]||d.stage}</span>
            <span class="flex-1 text-sm font-bold text-surface-900 dark:text-white">${d.title}</span>
            <span class="text-sm font-black text-emerald-600">฿${_fmt(d.value)}</span>
          </div>`).join('')||'<p class="text-xs text-surface-400">ยังไม่มี Deals</p>'}
        </div>
        <div><h4 class="text-xs font-black text-surface-500 uppercase tracking-wider mb-2">กิจกรรมล่าสุด</h4>
          ${acts.slice(0,5).map(a=>`<div class="flex gap-3 p-2 border-b border-surface-100 dark:border-surface-800">
            <span class="text-[10px] text-surface-400">${_fmtDate(a.created_at)}</span>
            <span class="text-xs text-surface-700 dark:text-surface-300">${a.content}</span>
          </div>`).join('')||'<p class="text-xs text-surface-400">ยังไม่มีกิจกรรม</p>'}
        </div>
        ${c.notes?`<div><h4 class="text-xs font-black text-surface-500 uppercase tracking-wider mb-1">หมายเหตุ</h4><p class="text-sm text-surface-600 dark:text-surface-300">${c.notes}</p></div>`:''}
      </div>
    </div>
  </div>`;
  const div = document.createElement('div'); div.innerHTML=html; document.body.appendChild(div);
}

function openCrmCustomerModal(cid=null) {
  const c = cid ? _crmCustomers.find(x=>x.id===cid) : null;
  const html = `
  <div class="fixed inset-0 z-[9999] bg-black/60 backdrop-blur-md flex items-center justify-center p-4" id="crmCustModal" onclick="if(event.target.id==='crmCustModal')this.remove()">
    <div class="bg-white dark:bg-surface-900 w-full max-w-lg rounded-3xl shadow-2xl">
      <div class="p-6 border-b border-surface-200 dark:border-surface-800 flex items-center justify-between">
        <h3 class="text-lg font-black text-surface-900 dark:text-white">${cid?'แก้ไข':'เพิ่ม'}ลูกค้า</h3>
        <button onclick="document.getElementById('crmCustModal').remove()" class="text-surface-400 hover:text-surface-600"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>
      </div>
      <div class="p-6 space-y-3">
        <div class="grid grid-cols-2 gap-3">
          <div><label class="text-xs font-bold text-surface-500 block mb-1">ชื่อ *</label><input id="crm-c-name" value="${c?.name||''}" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white"></div>
          <div><label class="text-xs font-bold text-surface-500 block mb-1">บริษัท</label><input id="crm-c-company" value="${c?.company||''}" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white"></div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div><label class="text-xs font-bold text-surface-500 block mb-1">อีเมล</label><input id="crm-c-email" value="${c?.email||''}" type="email" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white"></div>
          <div><label class="text-xs font-bold text-surface-500 block mb-1">โทรศัพท์</label><input id="crm-c-phone" value="${c?.phone||''}" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white"></div>
        </div>
        <div><label class="text-xs font-bold text-surface-500 block mb-1">เลขผู้เสียภาษี</label><input id="crm-c-tax" value="${c?.tax_id||''}" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white"></div>
        <div><label class="text-xs font-bold text-surface-500 block mb-1">ที่อยู่</label><textarea id="crm-c-addr" rows="2" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white resize-none">${c?.address||''}</textarea></div>
        <div><label class="text-xs font-bold text-surface-500 block mb-1">หมายเหตุ</label><textarea id="crm-c-notes" rows="2" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white resize-none">${c?.notes||''}</textarea></div>
      </div>
      <div class="p-6 border-t border-surface-200 dark:border-surface-800 flex gap-3 justify-end">
        <button onclick="document.getElementById('crmCustModal').remove()" class="px-4 py-2 text-sm font-bold text-surface-500 hover:bg-surface-100 rounded-xl transition">ยกเลิก</button>
        <button onclick="saveCrmCustomer(${cid||'null'})" class="px-6 py-2 bg-violet-600 hover:bg-violet-700 text-white text-sm font-bold rounded-xl transition">บันทึก</button>
      </div>
    </div>
  </div>`;
  const div=document.createElement('div'); div.innerHTML=html; document.body.appendChild(div);
}

async function saveCrmCustomer(cid) {
  const payload = {
    name: document.getElementById('crm-c-name')?.value?.trim(),
    company: document.getElementById('crm-c-company')?.value||'',
    email: document.getElementById('crm-c-email')?.value||'',
    phone: document.getElementById('crm-c-phone')?.value||'',
    tax_id: document.getElementById('crm-c-tax')?.value||'',
    address: document.getElementById('crm-c-addr')?.value||'',
    notes: document.getElementById('crm-c-notes')?.value||'',
  };
  if (!payload.name) { alert('กรุณากรอกชื่อ'); return; }
  const r = cid
    ? await _json(`/api/crm/customers/${cid}`, {method:'PUT', body:JSON.stringify(payload)})
    : await _json('/api/crm/customers', {method:'POST', body:JSON.stringify(payload)});
  if (r.ok) { document.getElementById('crmCustModal')?.remove(); loadCrmCustomers(); toast('บันทึกสำเร็จ','success'); }
  else toast(r.error||'Error','error');
}

async function deleteCrmCustomer(cid) {
  if (!confirm('ลบลูกค้านี้?')) return;
  await _json(`/api/crm/customers/${cid}`, {method:'DELETE'});
  loadCrmCustomers();
}

async function loadCrmDeals(stage='') {
  _crmDealFilter = stage;
  const url = `/api/crm/deals${stage?'?stage='+stage:''}`;
  const d = await _json(url);
  _crmDeals = d.deals||[];
  renderCrmDeals();
}

function crmFilterDeals(stage) { loadCrmDeals(stage); }

function renderCrmDeals() {
  const el = document.getElementById('crm-deals-list');
  if (!el) return;
  if (!_crmDeals.length) { el.innerHTML='<div class="py-12 text-center text-surface-400 text-sm">ยังไม่มี Deals</div>'; return; }
  el.innerHTML = _crmDeals.map(d=>`
    <div class="bg-white dark:bg-surface-900 rounded-2xl border border-surface-200 dark:border-surface-800 p-4 hover:shadow-md transition-all flex items-center gap-4">
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <span class="text-[10px] font-bold px-2 py-0.5 rounded-lg ${DEAL_COLORS[d.stage]||''}">${DEAL_STAGES[d.stage]||d.stage}</span>
          <h3 class="font-black text-sm text-surface-900 dark:text-white truncate">${d.title}</h3>
        </div>
        <p class="text-xs text-surface-400">${d.customer_name||'—'} ${d.customer_company?'('+d.customer_company+')':''}</p>
        ${d.expected_close?`<p class="text-[10px] text-surface-400 mt-0.5">กำหนดปิด: ${_fmtDate(d.expected_close)}</p>`:''}
      </div>
      <div class="text-right flex-shrink-0">
        <p class="font-black text-base text-emerald-600">฿${_fmt(d.value)}</p>
        <p class="text-[10px] text-surface-400">${d.probability||50}% probability</p>
      </div>
      <div class="flex gap-1">
        <button onclick="openCrmDealModal(${d.id})" class="p-2 hover:bg-surface-100 dark:hover:bg-surface-800 rounded-lg transition text-surface-400 hover:text-violet-500">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
        </button>
        <button onclick="deleteCrmDeal(${d.id})" class="p-2 hover:bg-surface-100 dark:hover:bg-surface-800 rounded-lg transition text-surface-400 hover:text-red-500">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
        </button>
      </div>
    </div>`).join('');
}

function openCrmDealModal(did=null) {
  const deal = did ? _crmDeals.find(x=>x.id===did) : null;
  const custOpts = _crmCustomers.map(c=>`<option value="${c.id}" ${deal?.customer_id===c.id?'selected':''}>${c.name}</option>`).join('');
  const html = `
  <div class="fixed inset-0 z-[9999] bg-black/60 backdrop-blur-md flex items-center justify-center p-4" id="crmDealModal" onclick="if(event.target.id==='crmDealModal')this.remove()">
    <div class="bg-white dark:bg-surface-900 w-full max-w-lg rounded-3xl shadow-2xl">
      <div class="p-6 border-b border-surface-200 dark:border-surface-800 flex items-center justify-between">
        <h3 class="text-lg font-black text-surface-900 dark:text-white">${did?'แก้ไข':'เพิ่ม'} Deal</h3>
        <button onclick="document.getElementById('crmDealModal').remove()" class="text-surface-400 hover:text-surface-600"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>
      </div>
      <div class="p-6 space-y-3">
        <div><label class="text-xs font-bold text-surface-500 block mb-1">ชื่อ Deal *</label><input id="crm-d-title" value="${deal?.title||''}" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white"></div>
        <div class="grid grid-cols-2 gap-3">
          <div><label class="text-xs font-bold text-surface-500 block mb-1">ลูกค้า</label>
            <select id="crm-d-cid" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white">
              <option value="">— ไม่ระบุ —</option>${custOpts}</select></div>
          <div><label class="text-xs font-bold text-surface-500 block mb-1">Stage</label>
            <select id="crm-d-stage" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white">
              ${Object.entries(DEAL_STAGES).map(([k,v])=>`<option value="${k}" ${deal?.stage===k?'selected':''}>${v}</option>`).join('')}
            </select></div>
        </div>
        <div class="grid grid-cols-3 gap-3">
          <div><label class="text-xs font-bold text-surface-500 block mb-1">มูลค่า (฿)</label><input id="crm-d-value" type="number" value="${deal?.value||0}" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white"></div>
          <div><label class="text-xs font-bold text-surface-500 block mb-1">Probability %</label><input id="crm-d-prob" type="number" value="${deal?.probability||50}" min="0" max="100" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white"></div>
          <div><label class="text-xs font-bold text-surface-500 block mb-1">กำหนดปิด</label><input id="crm-d-close" type="date" value="${deal?.expected_close||''}" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white"></div>
        </div>
        <div><label class="text-xs font-bold text-surface-500 block mb-1">ผู้รับผิดชอบ</label><input id="crm-d-assign" value="${deal?.assigned_to||''}" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white"></div>
        <div><label class="text-xs font-bold text-surface-500 block mb-1">หมายเหตุ</label><textarea id="crm-d-notes" rows="2" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white resize-none">${deal?.notes||''}</textarea></div>
      </div>
      <div class="p-6 border-t border-surface-200 dark:border-surface-800 flex gap-3 justify-end">
        <button onclick="document.getElementById('crmDealModal').remove()" class="px-4 py-2 text-sm font-bold text-surface-500 hover:bg-surface-100 rounded-xl transition">ยกเลิก</button>
        <button onclick="saveCrmDeal(${did||'null'})" class="px-6 py-2 bg-violet-600 hover:bg-violet-700 text-white text-sm font-bold rounded-xl transition">บันทึก</button>
      </div>
    </div>
  </div>`;
  const div=document.createElement('div'); div.innerHTML=html; document.body.appendChild(div);
}

async function saveCrmDeal(did) {
  const payload = {
    title: document.getElementById('crm-d-title')?.value?.trim(),
    customer_id: document.getElementById('crm-d-cid')?.value||null,
    stage: document.getElementById('crm-d-stage')?.value||'lead',
    value: parseFloat(document.getElementById('crm-d-value')?.value||0),
    probability: parseInt(document.getElementById('crm-d-prob')?.value||50),
    expected_close: document.getElementById('crm-d-close')?.value||'',
    assigned_to: document.getElementById('crm-d-assign')?.value||'',
    notes: document.getElementById('crm-d-notes')?.value||'',
  };
  if (!payload.title) { alert('กรุณากรอกชื่อ Deal'); return; }
  const r = did
    ? await _json(`/api/crm/deals/${did}`, {method:'PUT', body:JSON.stringify(payload)})
    : await _json('/api/crm/deals', {method:'POST', body:JSON.stringify(payload)});
  if (r.ok) { document.getElementById('crmDealModal')?.remove(); loadCrmDeals(_crmDealFilter); toast('บันทึกสำเร็จ','success'); }
  else toast(r.error||'Error','error');
}

async function deleteCrmDeal(did) {
  if (!confirm('ลบ Deal นี้?')) return;
  await _json(`/api/crm/deals/${did}`, {method:'DELETE'});
  loadCrmDeals(_crmDealFilter);
}

/* ════════════════════════════════════════════════
   WHT Certificate
   ════════════════════════════════════════════════ */
function initWhtView() {
  const sel = document.getElementById('wht-ym');
  if (!sel || sel.options.length > 0) { loadWhtSummary(); return; }
  const now = new Date();
  for (let i=0; i<12; i++) {
    const d = new Date(now.getFullYear(), now.getMonth()-i, 1);
    const val = d.toISOString().substring(0,7);
    const opt = document.createElement('option');
    opt.value = val;
    opt.textContent = val;
    if (i===0) opt.selected = true;
    sel.appendChild(opt);
  }
  loadWhtSummary();
}

async function loadWhtSummary() {
  const ym = document.getElementById('wht-ym')?.value || new Date().toISOString().substring(0,7);
  const d = await _json(`/api/wht/summary?ym=${ym}`);
  const el = document.getElementById('wht-table-body');
  const cards = document.getElementById('wht-summary-cards');
  if (cards) cards.innerHTML = `
    <div class="bg-white dark:bg-surface-900 rounded-2xl border border-surface-200 dark:border-surface-800 p-4 text-center">
      <p class="text-xs font-black text-surface-400 uppercase mb-1">รายการทั้งหมด</p>
      <p class="text-2xl font-black text-surface-900 dark:text-white">${(d.items||[]).length}</p>
    </div>
    <div class="bg-white dark:bg-surface-900 rounded-2xl border border-surface-200 dark:border-surface-800 p-4 text-center">
      <p class="text-xs font-black text-surface-400 uppercase mb-1">ยอดรวมค่าจ้าง</p>
      <p class="text-2xl font-black text-blue-600">฿${_fmt(d.total_base)}</p>
    </div>
    <div class="bg-white dark:bg-surface-900 rounded-2xl border border-surface-200 dark:border-surface-800 p-4 text-center">
      <p class="text-xs font-black text-surface-400 uppercase mb-1">ภาษีที่หักรวม</p>
      <p class="text-2xl font-black text-red-600">฿${_fmt(d.total_wht)}</p>
    </div>`;
  if (!el) return;
  if (!d.items?.length) {
    el.innerHTML='<tr><td colspan="6" class="px-4 py-8 text-center text-surface-400 text-xs">ไม่มีรายการหัก ณ ที่จ่ายในเดือนนี้ (กรอกใน expense claims โดยระบุ WHT)</td></tr>'; return;
  }
  const whtTypeMap = {'0.75':'ค่าจ้างแรงงาน','1':'ค่าขนส่ง','2':'ค่าโฆษณา','3':'ค่าบริการ','5':'ค่าเช่า','10':'วิชาชีพอิสระ','15':'เงินปันผล'};
  el.innerHTML = d.items.map(it=>`
    <tr class="border-b border-surface-100 dark:border-surface-800 hover:bg-surface-50 dark:hover:bg-surface-800/50">
      <td class="px-4 py-3 text-sm font-bold text-surface-900 dark:text-white">${it.vendor_name||'—'}</td>
      <td class="px-4 py-3 text-xs text-surface-400">${it.vendor_tax_id||'—'}</td>
      <td class="px-4 py-3 text-xs text-surface-600 dark:text-surface-300">${it.wht_type || whtTypeMap[String(Math.round(it.wht_rate))] || 'ค่าบริการ'}</td>
      <td class="px-4 py-3 text-sm text-right font-bold">฿${_fmt(it.amount)}</td>
      <td class="px-4 py-3 text-xs text-right text-surface-400">${it.wht_rate||0}%</td>
      <td class="px-4 py-3 text-sm text-right font-black text-red-600">฿${_fmt(it.wht_amount)}</td>
    </tr>`).join('');
}

async function downloadWhtPdf() {
  try {
    const ym = document.getElementById('wht-ym')?.value || new Date().toISOString().substring(0,7);
    toast('กำลังสร้างเอกสาร 50 ทวิ...', 'info');
    const resp = await fetch('/api/wht/pdf', {
      method:'POST', headers:{'Content-Type':'application/json'},
      credentials:'same-origin', body: JSON.stringify({year_month:ym})
    });
    if (!resp.ok) {
      let errMsg = 'สร้าง PDF ไม่สำเร็จ';
      try {
        const errJson = await resp.json();
        if (errJson && errJson.error) errMsg = errJson.error;
      } catch(e) {}
      toast(errMsg, 'error');
      return;
    }
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `WHT_${ym}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast('ดาวน์โหลดเอกสารสำเร็จแล้ว', 'success');
  } catch(err) {
    toast('เกิดข้อผิดพลาดในการดาวน์โหลด: ' + err.message, 'error');
  }
}

/* ════════════════════════════════════════════════
   MEETING NOTES
   ════════════════════════════════════════════════ */
async function loadMeetings() {
  const d = await _json('/api/meetings');
  const el = document.getElementById('meetings-list');
  if (!el) return;
  const meetings = d.meetings||[];
  if (!meetings.length) {
    el.innerHTML=`<div class="py-16 text-center text-surface-400">
      <svg class="w-12 h-12 mx-auto mb-4 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/></svg>
      <p class="text-sm font-semibold">ยังไม่มีบันทึกการประชุม</p></div>`; return;
  }
  el.innerHTML = meetings.map(m=>`
    <div class="bg-white dark:bg-surface-900 rounded-2xl border border-surface-200 dark:border-surface-800 p-5 hover:shadow-lg transition-all">
      <div class="flex items-start justify-between gap-4 mb-3">
        <div class="flex-1 min-w-0">
          <h3 class="font-black text-sm text-surface-900 dark:text-white truncate">${m.title}</h3>
          <div class="flex gap-3 mt-1">
            ${m.meeting_date?`<span class="text-xs text-surface-400">${m.meeting_date}</span>`:''}
            ${m.participants?`<span class="text-xs text-surface-400">${m.participants}</span>`:''}
          </div>
        </div>
        <div class="flex gap-1 flex-shrink-0">
          <button onclick="openMeetingDetail(${m.id})" class="p-2 hover:bg-surface-100 dark:hover:bg-surface-800 rounded-lg transition text-surface-400 hover:text-sky-500" title="ดูรายละเอียด">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
          </button>
          <button onclick="saveMeetingToWiki(${m.id})" class="p-2 hover:bg-surface-100 dark:hover:bg-surface-800 rounded-lg transition text-surface-400 hover:text-emerald-500" title="บันทึกลง Wiki">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
          </button>
          <button onclick="deleteMeeting(${m.id})" class="p-2 hover:bg-surface-100 dark:hover:bg-surface-800 rounded-lg transition text-surface-400 hover:text-red-500" title="ลบ">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
          </button>
        </div>
      </div>
      ${m.summary?`<p class="text-xs text-surface-500 dark:text-surface-400 line-clamp-2">${m.summary}</p>`:''}
      ${m.action_items?.length?`<div class="mt-3 pt-3 border-t border-surface-100 dark:border-surface-800">
        <p class="text-[10px] font-black text-surface-400 uppercase mb-1">Action Items (${m.action_items.length})</p>
        ${m.action_items.slice(0,2).map(a=>`<div class="flex items-center gap-2 text-xs text-surface-500">
          <div class="w-1.5 h-1.5 rounded-full bg-sky-400 flex-shrink-0"></div>${a.task||''}${a.assignee?' → '+a.assignee:''}
        </div>`).join('')}
        ${m.action_items.length>2?`<p class="text-[10px] text-surface-400 mt-1">+${m.action_items.length-2} รายการ</p>`:''}
      </div>`:''}
      ${m.wiki_page_id?'<div class="mt-2"><span class="text-[10px] bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-bold">✓ บันทึกใน Wiki แล้ว</span></div>':''}
    </div>`).join('');
}

async function openMeetingDetail(mid) {
  const d = await _json(`/api/meetings/${mid}`);
  const m = d.meeting;
  const html = `
  <div class="fixed inset-0 z-[9999] bg-black/60 backdrop-blur-md flex items-center justify-center p-4" id="meetingDetailModal" onclick="if(event.target.id==='meetingDetailModal')this.remove()">
    <div class="bg-white dark:bg-surface-900 w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-3xl shadow-2xl">
      <div class="p-6 border-b border-surface-200 dark:border-surface-800 flex items-center justify-between">
        <h3 class="text-lg font-black text-surface-900 dark:text-white">${m.title}</h3>
        <button onclick="document.getElementById('meetingDetailModal').remove()" class="text-surface-400 hover:text-surface-600"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>
      </div>
      <div class="p-6 space-y-4">
        <div class="grid grid-cols-2 gap-4 text-sm">
          <div><span class="text-xs font-bold text-surface-400 block">วันที่</span>${m.meeting_date||'—'}</div>
          <div><span class="text-xs font-bold text-surface-400 block">ผู้เข้าร่วม</span>${m.participants||'—'}</div>
        </div>
        ${m.summary?`<div><span class="text-xs font-black text-surface-400 uppercase tracking-wider block mb-2">สรุปประเด็น</span>
          <p class="text-sm text-surface-700 dark:text-surface-300 leading-relaxed whitespace-pre-line">${m.summary}</p></div>`:''}
        ${m.action_items?.length?`<div><span class="text-xs font-black text-surface-400 uppercase tracking-wider block mb-2">Action Items</span>
          ${m.action_items.map(a=>`<div class="flex items-start gap-2 p-2 bg-surface-50 dark:bg-surface-800 rounded-lg mb-1.5">
            <div class="w-2 h-2 rounded-full bg-sky-400 mt-1.5 flex-shrink-0"></div>
            <div class="flex-1"><p class="text-sm font-bold text-surface-900 dark:text-white">${a.task||''}</p>
              <p class="text-xs text-surface-400">${a.assignee?'ผู้รับผิดชอบ: '+a.assignee:''} ${a.due?'· กำหนด: '+a.due:''}</p></div>
          </div>`).join('')}</div>`:''}
        ${m.transcript?`<div><span class="text-xs font-black text-surface-400 uppercase tracking-wider block mb-2">ถอดเสียง (Transcript)</span>
          <div class="bg-surface-50 dark:bg-surface-800 rounded-xl p-4 max-h-48 overflow-y-auto">
            <p class="text-xs text-surface-600 dark:text-surface-300 leading-relaxed whitespace-pre-line">${m.transcript}</p>
          </div></div>`:''}
      </div>
      <div class="p-6 border-t border-surface-200 dark:border-surface-800 flex gap-3 justify-end">
        ${!m.wiki_page_id?`<button onclick="saveMeetingToWiki(${m.id});document.getElementById('meetingDetailModal').remove()" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-bold rounded-xl transition">บันทึกลง Wiki</button>`:''}
        <button onclick="document.getElementById('meetingDetailModal').remove()" class="px-4 py-2 text-sm font-bold text-surface-500 hover:bg-surface-100 rounded-xl transition">ปิด</button>
      </div>
    </div>
  </div>`;
  const div=document.createElement('div'); div.innerHTML=html; document.body.appendChild(div);
}

function openMeetingUploadModal() {
  const html = `
  <div class="fixed inset-0 z-[9999] bg-black/60 backdrop-blur-md flex items-center justify-center p-4" id="meetingUpModal" onclick="if(event.target.id==='meetingUpModal')this.remove()">
    <div class="bg-white dark:bg-surface-900 w-full max-w-lg rounded-3xl shadow-2xl">
      <div class="p-6 border-b border-surface-200 dark:border-surface-800 flex items-center justify-between">
        <h3 class="text-lg font-black text-surface-900 dark:text-white">อัปโหลดไฟล์เสียงการประชุม</h3>
        <button onclick="document.getElementById('meetingUpModal').remove()" class="text-surface-400 hover:text-surface-600"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>
      </div>
      <div class="p-6 space-y-4">
        <div><label class="text-xs font-bold text-surface-500 block mb-1">หัวข้อการประชุม *</label>
          <input id="mt-title" type="text" placeholder="เช่น ประชุมทีม Q2 2026" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white"></div>
        <div class="grid grid-cols-2 gap-3">
          <div><label class="text-xs font-bold text-surface-500 block mb-1">วันที่ประชุม</label>
            <input id="mt-date" type="date" value="${new Date().toISOString().substring(0,10)}" class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white"></div>
          <div><label class="text-xs font-bold text-surface-500 block mb-1">ผู้เข้าร่วม</label>
            <input id="mt-participants" type="text" placeholder="สมชาย, สมหญิง, ..." class="w-full px-3 py-2 text-sm border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800 text-surface-900 dark:text-white"></div>
        </div>
        <div>
          <label class="text-xs font-bold text-surface-500 block mb-1">ไฟล์เสียง (mp3, wav, m4a, ogg, webm)</label>
          <label class="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-surface-300 dark:border-surface-700 rounded-2xl cursor-pointer hover:border-sky-400 transition">
            <svg class="w-8 h-8 text-surface-300 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/></svg>
            <span id="mt-file-label" class="text-xs text-surface-400">คลิกเพื่อเลือกไฟล์</span>
            <input id="mt-file" type="file" accept=".mp3,.mp4,.wav,.ogg,.m4a,.webm,.aac" class="hidden" onchange="document.getElementById('mt-file-label').textContent=this.files[0]?.name||'คลิกเพื่อเลือกไฟล์'">
          </label>
        </div>
        <div id="mt-progress" class="hidden">
          <div class="w-full bg-surface-100 dark:bg-surface-800 rounded-full h-1.5 mb-1.5">
            <div class="h-full bg-sky-500 rounded-full animate-pulse" style="width:100%"></div>
          </div>
          <p class="text-xs text-center text-sky-500 font-bold">กำลังประมวลผลด้วย AI... อาจใช้เวลา 30-120 วินาที</p>
        </div>
      </div>
      <div class="p-6 border-t border-surface-200 dark:border-surface-800 flex gap-3 justify-end">
        <button onclick="document.getElementById('meetingUpModal').remove()" class="px-4 py-2 text-sm font-bold text-surface-500 hover:bg-surface-100 rounded-xl transition">ยกเลิก</button>
        <button onclick="uploadMeeting()" class="px-6 py-2 bg-sky-600 hover:bg-sky-700 text-white text-sm font-bold rounded-xl transition flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
          อัปโหลดและวิเคราะห์
        </button>
      </div>
    </div>
  </div>`;
  const div=document.createElement('div'); div.innerHTML=html; document.body.appendChild(div);
}

async function uploadMeeting() {
  const title = document.getElementById('mt-title')?.value?.trim();
  const file  = document.getElementById('mt-file')?.files?.[0];
  if (!title) { alert('กรุณากรอกหัวข้อการประชุม'); return; }
  if (!file)  { alert('กรุณาเลือกไฟล์เสียง'); return; }

  document.getElementById('mt-progress')?.classList.remove('hidden');
  document.querySelector('#meetingUpModal button[onclick="uploadMeeting()"]').disabled = true;
  
  showGlobalLoading('กำลังอัปโหลดและวิเคราะห์การประชุมด้วย AI...');

  const form = new FormData();
  form.append('audio', file);
  form.append('title', title);
  form.append('meeting_date', document.getElementById('mt-date')?.value||'');
  form.append('participants', document.getElementById('mt-participants')?.value||'');

  try {
    const resp = await fetch('/api/meetings/upload', {method:'POST', credentials:'same-origin', body:form});
    const d = await resp.json();
    if (d.ok) {
      document.getElementById('meetingUpModal')?.remove();
      toast('วิเคราะห์การประชุมสำเร็จ!','success');
      loadMeetings();
    } else {
      toast(d.error||'เกิดข้อผิดพลาด','error');
    }
  } catch(e) {
    toast('ไม่สามารถเชื่อมต่อได้','error');
  } finally {
    document.getElementById('mt-progress')?.classList.add('hidden');
    hideGlobalLoading();
  }
}

async function saveMeetingToWiki(mid) {
  const r = await _json(`/api/meetings/${mid}/save-to-wiki`, {method:'POST', body:'{}'});
  if (r.ok) { toast('บันทึกลง Wiki แล้ว','success'); loadMeetings(); }
  else toast(r.error||'Error','error');
}

async function deleteMeeting(mid) {
  if (!confirm('ลบบันทึกนี้?')) return;
  await _json(`/api/meetings/${mid}`, {method:'DELETE'});
  loadMeetings();
}
