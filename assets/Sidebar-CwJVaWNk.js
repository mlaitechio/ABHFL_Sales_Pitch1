import{j as e,u as R,a as b,r as h,A as v,c as w,i as N,k as m,m as k,f as q,v as H,l as P,h as Y,e as $}from"./index-PgtJCQgL.js";import{P as C}from"./index-DoLHaob8.js";import"./CloseIcon-CNXAojed.js";import{L as z}from"./logo-DauWxPY-.js";function x(){return e.jsx("svg",{xmlns:"http://www.w3.org/2000/svg",width:"1rem",height:"1rem",viewBox:"0 0 24 24",children:e.jsx("path",{fill:"none",stroke:"black",strokeLinecap:"round",strokeLinejoin:"round",strokeWidth:2,d:"M8 9h8m-8 4h6m-5 5H6a3 3 0 0 1-3-3V7a3 3 0 0 1 3-3h12a3 3 0 0 1 3 3v8a3 3 0 0 1-3 3h-3l-3 3z"})})}const T=(i=0)=>{const o=new Date;return o.setDate(o.getDate()+i),o.toISOString().split("T")[0]},F=({handleStopNewChat:i,HF_email:o})=>{const c=R(),D=b(s=>s.sidebar.state),f=b(s=>s.chats.chats),[y,S]=h.useState([]),[g,G]=h.useState([]),[u,E]=h.useState([]),[j,L]=h.useState([]),p=async s=>{i();try{const t=`${v}/history/`,n={"Content-Type":"application/json"},l={HF_email:o,session:s},{data:d}=await w.post(t,l,{header:n});c(N()),c(m(s));const a=[];d.forEach(r=>{const B={id:r.ques_id,message:r.answer,type:k.bot,timestamp:r.outputTimestamp,feedback:r.feedback?r.feedback:q.neutral},_={id:H(),message:r.message,type:k.user,timestamp:r.inputTimestamp};a.push(_),a.push(B)}),c(P(a))}catch(t){console.error(t)}},A=async()=>{c(Y()),c($()),c(m("")),c(N()),i()};return h.useEffect(()=>{const s=async()=>{try{const t=`${v}/history/`,n={"Content-Type":"application/json"},l={HF_email:o},{data:d}=await w.post(t,l,{header:n}),a=d.filter(r=>r.first_message!=="");L(a)}catch(t){console.error(t)}};o.length>0&&f.length%2===0&&s()},[o,f]),h.useEffect(()=>{const s=T(0),t=T(-1),n=[],l=[],d=[];j.forEach(a=>{var r;a.created_on.split("T")[0]===s?n.push(a):((r=a==null?void 0:a.created_on)==null?void 0:r.split("T")[0])===t?l.push(a):d.push(a)}),S(n),G(l),E(d)},[j]),e.jsxs("section",{className:`h-[100dvh] lg:h-screen bg-white rounded-lg w-72 p-4 ${D?"flex":"hidden"} lg:flex flex-col gap-4 absolute z-40 left-0 top-0 lg:relative shadow-md lg:shadow-none`,children:[e.jsxs("div",{className:"flex flex-col items-center gap-2",children:[e.jsx("img",{src:z,alt:"logo",className:"w-28"}),e.jsx("button",{className:"bg-[#FFE4D4] text-primary w-40 h-10 rounded hover:bg-primary hover:bg-opacity-35",onClick:A,children:"+ New Chat"})]}),e.jsx("div",{className:"border border-borderGrey"}),e.jsx("div",{className:"flex justify-between",children:e.jsx("p",{className:"text-headGrey",children:"Your Conversations"})}),e.jsx("div",{className:"border border-borderGrey"}),e.jsxs("div",{className:"flex flex-col gap-6 flex-1 overflow-x-hidden overflow-y-auto",children:[e.jsxs("div",{className:"flex flex-col gap-1",children:[e.jsx("p",{className:"text-headGrey font-bold",children:"Today"}),e.jsxs("div",{className:"flex-1 min-h-10 flex flex-col",children:[y.map(s=>e.jsxs("button",{className:"flex gap-2 items-center hover:bg-gray-100 p-1 rounded mr-3 overflow-hidden",onClick:()=>p(s==null?void 0:s.sessionid),children:[e.jsx("div",{children:e.jsx(x,{})}),e.jsx("p",{className:"whitespace-nowrap",children:s==null?void 0:s.first_message})]},s==null?void 0:s.sessionid)),!y.length&&e.jsx("p",{className:"pl-2 text-headGrey font-semibold text-sm",children:"No history yet"})]})]}),e.jsxs("div",{className:"flex flex-col gap-1",children:[e.jsx("p",{className:"text-headGrey font-bold",children:"Yesterday"}),e.jsxs("div",{className:"flex-1 min-h-10 flex flex-col",children:[g.map(s=>e.jsxs("button",{className:"flex gap-2 items-center hover:bg-gray-100 p-1 rounded mr-3 overflow-hidden",onClick:()=>p(s==null?void 0:s.sessionid),children:[e.jsx("div",{children:e.jsx(x,{})}),e.jsx("p",{className:"whitespace-nowrap",children:s==null?void 0:s.first_message})]},s==null?void 0:s.sessionid)),!g.length&&e.jsx("p",{className:"pl-2 text-headGrey font-semibold text-sm",children:"No history yet"})]})]}),e.jsxs("div",{className:"flex flex-col gap-1",children:[e.jsx("p",{className:"text-headGrey font-bold",children:"Previous 7 days"}),e.jsxs("div",{className:"flex-1 min-h-10 flex flex-col",children:[u.map(s=>e.jsxs("button",{className:"flex gap-2 items-center hover:bg-gray-100 p-1 rounded mr-3 overflow-hidden",onClick:()=>p(s==null?void 0:s.sessionid),children:[e.jsx("div",{children:e.jsx(x,{})}),e.jsx("p",{className:"whitespace-nowrap",children:s==null?void 0:s.first_message})]},s==null?void 0:s.sessionid)),!u.length&&e.jsx("p",{className:"pl-2 text-headGrey font-semibold text-sm",children:"No history yet"})]})]})]})]})};F.propTypes={handleStopNewChat:C.func,HF_email:C.string};export{F as default};