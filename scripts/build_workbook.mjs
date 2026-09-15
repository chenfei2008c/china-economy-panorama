import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const payload=JSON.parse(await fs.readFile(path.join(root,'data/workbook.json'),'utf8'));
const calc=JSON.parse(await fs.readFile(path.join(root,'data/calculation_cases.json'),'utf8'));
const wb=Workbook.create();
const navy='#18354A',teal='#167D8D',pale='#EAF2F5',ink='#243746';
const previewDir=path.join(root,'validation/previews');
await fs.mkdir(previewDir,{recursive:true});
function col(n){let s='';for(n++;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;}
function visualLength(v){return [...String(v)].reduce((n,c)=>n+(/[\u0000-\u00ff]/.test(c)?0.55:1),0);}
const index={};
for(let si=0;si<payload.sheets.length;si++){
  const spec=payload.sheets[si],sh=wb.worksheets.add(spec.name);index[spec.name]=sh;
  sh.showGridLines=false;sh.tabColor=si===0?teal:navy;
  const end=spec.rows.length+5,last=col(spec.headers.length-1);
  const body=sh.getRange(`A1:${last}${end}`);
  body.format.font={name:'Arial',size:11,color:ink};
  body.format.verticalAlignment='top';body.format.wrapText=true;
  body.setNumberFormat('@');
  sh.getRange('A1:F2').merge();sh.getRange('A1').values=[[spec.name+'  /  中国经济全景']];
  sh.getRange('A1:F2').format.fill=navy;
  sh.getRange('A1:F2').format.font={name:'Arial',size:21,bold:true,color:'#FFFFFF'};
  sh.getRange('A1:F2').format.verticalAlignment='center';
  sh.getRange('A1:F2').format.rowHeightPx=30;
  sh.getRange('A3:H3').merge();sh.getRange('A3').values=[[spec.subtitle]];
  sh.getRange('A3:H3').format.font={name:'Arial',size:11,color:'#526C7E'};
  sh.getRange('A3:H3').format.rowHeightPx=35;
  sh.getRange('A4:H4').merge();sh.getRange('A4').values=[['版本 1.0.0 · 核验日 2026-09-15 · 数据报告期按来源登记 · 筛选查看，固定问题/指标编号']];
  sh.getRange('A4:H4').format.rowHeightPx=29;
  sh.getRange(`A5:${last}5`).values=[spec.headers];
  sh.getRange(`A6:${last}${end}`).values=spec.rows.map(r=>r.map(v=>String(v).startsWith('=')?"'"+v:v));
  const table=sh.tables.add(`A5:${last}${end}`,true,`PanoramaTable${si+1}`);
  table.style='TableStyleLight1';table.showFilterButton=true;
  sh.getRange(`A5:${last}5`).format.fill=navy;
  sh.getRange(`A5:${last}5`).format.font={name:'Arial',size:11,bold:true,color:'#FFFFFF'};
  sh.getRange(`A5:${last}5`).format.rowHeightPx=38;
  for(let c=0;c<spec.headers.length;c++)sh.getRange(`${col(c)}1:${col(c)}${end}`).format.columnWidthPx=spec.widths[c]||200;
  for(let r=0;r<spec.rows.length;r++){
    const rn=r+6,rg=sh.getRange(`A${rn}:${last}${rn}`);
    // Keep Chinese prose readable at normal zoom; only maximum Excel row height
    // is a cap. Text is not shortened or moved into hidden cells.
    const lines=Math.max(...spec.rows[r].map((v,c)=>Math.ceil(visualLength(v)/Math.max(4,((spec.widths[c]||200)-16)/14))));
    rg.format.rowHeightPx=Math.max(46,Math.min(540,lines*18+14));
    if(r%2===1)rg.format.fill='#F1F6F8';
  }
  sh.getRange(`A6:B${end}`).format.font={name:'Arial',size:11,bold:true,color:'#185777'};
  sh.freezePanes.freezeRows(5);sh.freezePanes.freezeColumns(2);
  if(spec.name==='全景模板'){
    sh.getRange('D6:G19').format.fill='#FFF4D9';
    sh.getRange('F6:F12').dataValidation={rule:{type:'list',values:['多环节支持','部分支持','相互矛盾','证据不足']}};
  }
  console.log('Built',spec.name,spec.rows.length,'rows');
}

const rule=index['判断规则'];
let r=payload.sheets.find(s=>s.name==='判断规则').rows.length+9;
const calcStart=r;
rule.getRange(`A${r}:H${r}`).merge();rule.getRange(`A${r}`).values=[['公开输入与可复算样例（金额/比例口径以各例为准）']];
rule.getRange(`A${r}:H${r}`).format.fill=teal;rule.getRange(`A${r}:H${r}`).format.font={bold:true,color:'#FFFFFF',size:14};rule.getRange(`A${r}:H${r}`).format.rowHeightPx=36;r+=2;
const formulaManifest=[];
for(const c of calc){
  const heading=r;
  rule.getRange(`A${r}:H${r}`).merge();rule.getRange(`A${r}`).values=[[c.id+' · '+c.title+' · '+c.period]];
  rule.getRange(`A${r}:H${r}`).format.fill=pale;rule.getRange(`A${r}:H${r}`).format.font={bold:true,color:navy,size:12};rule.getRange(`A${r}:H${r}`).format.rowHeightPx=36;r++;
  rule.getRange(`A${r}:H${r}`).values=[['输入编号','公开原值','输入含义','单位','来源/原文位置','样本/比较口径','结果/公式','结果含义']];
  rule.getRange(`A${r}:H${r}`).format.fill=navy;rule.getRange(`A${r}:H${r}`).format.font={color:'#FFFFFF',bold:true};rule.getRange(`A${r}:H${r}`).format.rowHeightPx=34;r++;
  const inputStart=r;
  for(let j=0;j<c.inputs.length;j++,r++){
    const x=c.inputs[j];
    rule.getRange(`A${r}:H${r}`).values=[[x.metric_id,x.value,x.name,x.unit,x.source+' · '+x.location,c.scope,'','']];
    rule.getRange(`B${r}`).setNumberFormat('#,##0.0000;[Red](#,##0.0000);0.0000');
    rule.getRange(`B${r}`).format.fill='#E3F0E9';
    rule.getRange(`A${r}:H${r}`).format.rowHeightPx=65;
  }
  for(const o of c.outputs){
    const formula='='+o.expression.replace(/\bx(\d+)\b/g,(_,n)=>`B${inputStart+Number(n)}`);
    rule.getRange(`G${r}`).formulas=[[formula]];
    rule.getRange(`G${r}`).setNumberFormat('0.0000;[Red](0.0000);0.0000');
    rule.getRange(`A${r}:F${r}`).merge();rule.getRange(`A${r}`).values=[[o.metric_id+' · '+o.name]];
    rule.getRange(`H${r}`).values=[[o.unit+'；'+o.meaning]];
    rule.getRange(`A${r}:H${r}`).format.fill='#E1F2F2';rule.getRange(`A${r}:H${r}`).format.rowHeightPx=70;
    formulaManifest.push({case:c.id,metric_id:o.metric_id,cell:`判断规则!G${r}`,formula,expected:o.expected,tolerance:o.tolerance||0.000001});r++;
  }
  rule.getRange(`A${r}:H${r}`).merge();rule.getRange(`A${r}`).values=[['边界：'+c.boundary]];
  rule.getRange(`A${r}:H${r}`).format.rowHeightPx=58;r+=2;
}
rule.getRange(`A${calcStart}:H${r}`).format.wrapText=true;
rule.getRange(`A${calcStart}:H${r}`).format.verticalAlignment='center';
wb.recalculate();
const checks=await wb.inspect({kind:'formula',sheetId:'判断规则',range:`A${calcStart}:H${r}`,maxChars:2200,options:{maxResults:6}});
console.log(checks.ndjson||JSON.stringify(checks));
await fs.writeFile(path.join(root,'validation/formula_manifest.json'),JSON.stringify(formulaManifest,null,2));
for(const spec of payload.sheets){
  const preview=await wb.render({sheetName:spec.name,range:'A1:H8',scale:1,format:'png'});
  await fs.writeFile(path.join(previewDir,spec.name+'.png'),new Uint8Array(await preview.arrayBuffer()));
}
const preview=await wb.render({sheetName:'判断规则',range:`A${calcStart}:H${calcStart+10}`,scale:1,format:'png'});
await fs.writeFile(path.join(previewDir,'计算样例.png'),new Uint8Array(await preview.arrayBuffer()));
const out=await SpreadsheetFile.exportXlsx(wb);await out.save(path.join(root,'中国经济全景指标字典.xlsx'));
console.log('Exported 中国经济全景指标字典.xlsx',formulaManifest.length,'formulas');
