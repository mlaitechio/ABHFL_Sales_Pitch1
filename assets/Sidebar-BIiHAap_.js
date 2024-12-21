import{j as s,d as R,u as B,a as S,r as c,A as _,b as E}from"./index-BXJA53Pn.js";import{L as V}from"./logo-DauWxPY-.js";import{u as O}from"./useQuery-BHIhq6jP.js";import{u as Q}from"./useSidebar-BXGiJA6s.js";import{a as T,u as Y}from"./useToggle-C9Zy_hAv.js";const M=()=>s.jsxs("svg",{xmlns:"http://www.w3.org/2000/svg",width:"16",height:"16",viewBox:"0 0 16 16",children:[s.jsx("rect",{width:"16",height:"16",fill:"none"}),s.jsx("path",{fill:"#fd0000",fillRule:"evenodd",d:"M9 2H7a.5.5 0 0 0-.5.5V3h3v-.5A.5.5 0 0 0 9 2m2 1v-.5a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2V3H2.251a.75.75 0 0 0 0 1.5h.312l.317 7.625A3 3 0 0 0 5.878 15h4.245a3 3 0 0 0 2.997-2.875l.318-7.625h.312a.75.75 0 0 0 0-1.5zm.936 1.5H4.064l.315 7.562A1.5 1.5 0 0 0 5.878 13.5h4.245a1.5 1.5 0 0 0 1.498-1.438zm-6.186 2v5a.75.75 0 0 0 1.5 0v-5a.75.75 0 0 0-1.5 0m3.75-.75a.75.75 0 0 1 .75.75v5a.75.75 0 0 1-1.5 0v-5a.75.75 0 0 1 .75-.75",clipRule:"evenodd"})]}),P=()=>s.jsx("svg",{xmlns:"http://www.w3.org/2000/svg",width:"24",height:"24",viewBox:"0 0 24 24",children:s.jsx("path",{fill:"#000",d:"M12 10a2 2 0 1 0 2 2a2 2 0 0 0-2-2m-7 0a2 2 0 1 0 2 2a2 2 0 0 0-2-2m14 0a2 2 0 1 0 2 2a2 2 0 0 0-2-2"})});function I(){return s.jsx("svg",{xmlns:"http://www.w3.org/2000/svg",width:"1rem",height:"1rem",viewBox:"0 0 24 24",children:s.jsx("path",{fill:"none",stroke:"black",strokeLinecap:"round",strokeLinejoin:"round",strokeWidth:2,d:"M8 9h8m-8 4h6m-5 5H6a3 3 0 0 1-3-3V7a3 3 0 0 1 3-3h12a3 3 0 0 1 3 3v8a3 3 0 0 1-3 3h-3l-3 3z"})})}const F=()=>s.jsxs("svg",{xmlns:"http://www.w3.org/2000/svg",width:"16",height:"16",viewBox:"0 0 24 24",children:[s.jsx("rect",{width:"24",height:"24",fill:"none"}),s.jsx("path",{fill:"#000000",fillRule:"evenodd",d:"M14.757 2.621a4.682 4.682 0 0 1 6.622 6.622l-9.486 9.486c-.542.542-.86.86-1.216 1.137q-.628.492-1.35.835c-.406.193-.834.336-1.56.578l-3.332 1.11l-.802.268a1.81 1.81 0 0 1-2.29-2.29l1.378-4.133c.242-.727.385-1.155.578-1.562q.344-.72.835-1.35c.276-.354.595-.673 1.137-1.215zM4.4 20.821l2.841-.948c.791-.264 1.127-.377 1.44-.526q.572-.274 1.073-.663c.273-.214.525-.463 1.115-1.053l7.57-7.57a7.36 7.36 0 0 1-2.757-1.744A7.36 7.36 0 0 1 13.94 5.56l-7.57 7.57c-.59.589-.84.84-1.053 1.114q-.39.5-.663 1.073c-.149.313-.262.649-.526 1.44L3.18 19.6zM15.155 4.343c.035.175.092.413.189.69a5.86 5.86 0 0 0 1.4 2.222a5.86 5.86 0 0 0 2.221 1.4c.278.097.516.154.691.189l.662-.662a3.182 3.182 0 0 0-4.5-4.5z",clipRule:"evenodd"})]}),U=({handleEdit:e,handleDelete:n,atEnd:p})=>s.jsxs("div",{className:`absolute ${p?"bottom-1/2":"top-1/2"} right-0 z-50 flex flex-col border bg-white p-0.5 rounded-lg`,children:[s.jsxs("button",{className:"flex gap-2 hover:bg-gray-100 p-2 items-center rounded",onClick:i=>{i.stopPropagation(),e()},children:[s.jsx(F,{}),s.jsx("p",{className:"text-sm",children:"Edit"})]}),s.jsxs("button",{className:"flex gap-2 hover:bg-gray-100 p-2 items-center rounded",onClick:i=>{i.stopPropagation(),n()},children:[s.jsx(M,{}),s.jsx("p",{className:"text-red-500 text-sm",children:"Delete"})]})]}),H=({item:e,modalFor:n,getHistory:p,handleOpenModal:i,handleStopNewChat:f,atEnd:m})=>{const{HF_email:k}=R(),{session:N,setSession:q}=B(),{clearChats:y}=S(),{toggleHistory:w}=T(),l=c.useRef(null),C=c.useRef(null),[g,j]=c.useState(""),[v,a]=c.useState(!1);c.useEffect(()=>{e.session_name&&j(e.session_name)},[e]);const h=()=>{a(!0),g||j(e.first_message),i(void 0),setTimeout(()=>{var t;(t=C.current)==null||t.focus()},0)},o=async()=>{try{const t=`${_}/history/`,d={data:{HF_email:k,session:e.sessionid}};await E.delete(t,d),e.sessionid===N&&(q(""),y(),f()),w()}catch(t){console.log(t)}i(void 0)},r=async()=>{try{const t=`${_}/rename_session/`,d={session_id:e==null?void 0:e.sessionid,session_name:g},{data:x}=await E.patch(t,d);w(),console.log(x)}catch(t){console.log(t)}a(!1)},u=c.useCallback(t=>{l.current&&!l.current.contains(t.target)&&i(void 0)},[i]);return c.useEffect(()=>(document.addEventListener("mousedown",u),()=>{document.removeEventListener("mousedown",u)}),[u]),s.jsx(s.Fragment,{children:s.jsxs("div",{className:`flex gap-2 items-center hover:bg-gray-100 p-1 rounded mr-3 group justify-between relative cursor-pointer ${(n==null?void 0:n.sessionid)===e.sessionid?"bg-gray-100":""}`,onClick:()=>p(e==null?void 0:e.sessionid),children:[s.jsxs("div",{className:"flex items-center gap-2 overflow-hidden",children:[s.jsx("div",{children:s.jsx(I,{})}),v?s.jsxs("form",{onSubmit:t=>{t.preventDefault(),r()},children:[s.jsx("input",{ref:C,type:"text",value:g,onChange:t=>j(t.target.value),className:"border-b-2 border-primary bg-white px-2",onClick:t=>t.stopPropagation(),onBlur:r}),s.jsx("button",{className:"hidden",children:"Submit"})]}):s.jsx("p",{className:"whitespace-nowrap truncate",children:g||(e==null?void 0:e.first_message)})]}),!v&&s.jsx("button",{className:"group-hover:flex hidden",onClick:t=>{t.stopPropagation(),i(e)},children:s.jsx(P,{})}),(n==null?void 0:n.sessionid)===e.sessionid&&s.jsx("div",{ref:l,children:s.jsx(U,{handleEdit:h,handleDelete:o,atEnd:m})})]},e==null?void 0:e.sessionid)})},z=(e=0)=>{const n=new Date;return n.setDate(n.getDate()+e),n.toISOString().split("T")[0]},W=({handleStopNewChat:e})=>{const{chats:n,clearChats:p,historyChat:i}=S(),{setSession:f}=B(),{HF_email:m}=R(),{historyState:k}=T(),[N,q]=c.useState([]),[y,w]=c.useState([]),[l,C]=c.useState([]),[g,j]=c.useState(),v=o=>{j(o)},a=async o=>{e();try{const r=`${_}/history/`,u={HF_email:m,session:o},{data:t}=await E.post(r,u);p(),f(o);const d=[];t.forEach(x=>{const D={id:x.ques_id,answer:x.output,message:x.input_prompt,outputTimestamp:x.output_timestamp,inputTimestamp:x.input_prompt_timestamp,feedback:x.feedback?x.feedback:"neutral"};d.push(D)}),i(d)}catch(r){console.error(r)}},h=o=>{var r,u,t;return l.length+N.length+y.length>3&&(((r=l[l.length-1])==null?void 0:r.sessionid)===o.sessionid||((u=l[l.length-2])==null?void 0:u.sessionid)===o.sessionid||((t=l[l.length-3])==null?void 0:t.sessionid)===o.sessionid)};return c.useEffect(()=>{const o=async()=>{try{const r=`${_}/history/`,u={HF_email:m},{data:t}=await E.post(r,u),d=t.filter(b=>b.first_message!==""),x=z(0),D=z(-1),$=[],A=[],G=[];d.forEach(b=>{var L;b.created_on.split("T")[0]===x?$.push(b):((L=b==null?void 0:b.created_on)==null?void 0:L.split("T")[0])===D?A.push(b):G.push(b)}),q($),w(A),C(G)}catch(r){console.error(r)}};m.length!==0&&o()},[m,n,k]),s.jsxs("div",{className:"h-full overflow-hidden",children:[s.jsx("p",{className:"text-headGrey font-bold text-lg",children:"History"}),s.jsxs("div",{className:"h-full flex flex-col gap-6 flex-1 overflow-x-hidden overflow-y-auto pb-6",children:[s.jsxs("div",{className:"flex flex-col gap-1",children:[s.jsx("p",{className:"text-headGrey font-bold",children:"Today"}),s.jsxs("div",{className:"flex-1 min-h-10 flex flex-col",children:[N.map(o=>s.jsx(H,{modalFor:g,handleOpenModal:v,getHistory:a,item:o,handleStopNewChat:e,atEnd:h(o)},o.sessionid)),!N.length&&s.jsx("p",{className:"pl-2 text-headGrey font-semibold text-sm",children:"No history yet"})]})]}),s.jsxs("div",{className:"flex flex-col gap-1",children:[s.jsx("p",{className:"text-headGrey font-bold",children:"Yesterday"}),s.jsxs("div",{className:"flex-1 min-h-10 flex flex-col",children:[y.map(o=>s.jsx(H,{modalFor:g,handleOpenModal:v,getHistory:a,item:o,handleStopNewChat:e,atEnd:h(o)},o.sessionid)),!y.length&&s.jsx("p",{className:"pl-2 text-headGrey font-semibold text-sm",children:"No history yet"})]})]}),s.jsxs("div",{className:"flex flex-col gap-1",children:[s.jsx("p",{className:"text-headGrey font-bold",children:"Previous 7 days"}),s.jsxs("div",{className:"flex-1 min-h-10 flex flex-col",children:[l.map(o=>s.jsx(H,{modalFor:g,handleOpenModal:v,getHistory:a,item:o,handleStopNewChat:e,atEnd:h(o)},o.sessionid)),!l.length&&s.jsx("p",{className:"pl-2 text-headGrey font-semibold text-sm",children:"No history yet"})]})]})]})]})},J=({handleDelete:e,item:n,atEnd:p})=>s.jsx("div",{className:`absolute ${p?"bottom-1/2":"top-1/2"} right-0 z-50 flex flex-col border bg-white p-0.5 rounded-lg`,children:s.jsxs("button",{className:"flex gap-2 hover:bg-gray-100 p-2 items-center rounded",onClick:i=>{i.stopPropagation(),e(n)},children:[s.jsx(M,{}),s.jsx("p",{className:"text-red-500 text-sm",children:"Delete"})]})}),K=({handleStopNewChat:e})=>{const{bookmarks:n,getBookmark:p,setBookmarkId:i}=Y(),{HF_email:f}=R(),{bookmarkState:m}=T(),{clearChats:k,historyChat:N}=S(),{setSession:q}=B(),y=c.useRef(null),[w,l]=c.useState(),C=async(a,h)=>{e();try{const o=`${_}/history/`,r={HF_email:f,session:a},{data:u}=await E.post(o,r);k(),q(a);const t=[];u.forEach(d=>{const x={id:d.ques_id,answer:d.output,message:d.input_prompt,outputTimestamp:d.output_timestamp,inputTimestamp:d.input_prompt_timestamp,feedback:d.feedback?d.feedback:"neutral"};t.push(x)}),i(h),N(t)}catch(o){console.error(o)}},g=async a=>{try{const h=`${_}/bookmark/`,o={data:{ques_id:a.ques_id,session_id:a.session}};await E.delete(h,o),v()}catch(h){console.log(h)}},j=c.useCallback(a=>{y.current&&!y.current.contains(a.target)&&l(void 0)},[]);c.useEffect(()=>(document.addEventListener("mousedown",j),()=>{document.removeEventListener("mousedown",j)}),[j]);const v=c.useCallback(async()=>{try{const a=`${_}/bookmark/?HF_id=${f}`,{data:h}=await E.get(a),o=[];h.forEach(r=>{const u=r.session_name;r.bookmarks.forEach(t=>{o.push({ques_id:t.ques_id,additional_comments:t.additional_comments,created_on:t.created_on,feedback:t.feedback,input_prompt:t.input_prompt,output:t.output,session:u})})}),p(o)}catch(a){console.log(a)}},[f,p]);return c.useEffect(()=>{f&&v()},[f,v,m]),s.jsxs("div",{children:[s.jsx("p",{className:"text-headGrey font-bold text-lg",children:"Bookmarks"}),s.jsxs("div",{className:"max-h-[200px] min-h-[100px] overflow-y-auto",children:[n.map(a=>s.jsxs("div",{className:"flex gap-2 items-center hover:bg-gray-100 p-1 rounded mr-3 group justify-between relative cursor-pointer",onClick:()=>C(a.session,a.ques_id),children:[s.jsxs("div",{className:"flex items-center gap-2 overflow-hidden",children:[s.jsx("div",{children:s.jsx(I,{})}),s.jsx("p",{className:"whitespace-nowrap truncate",children:a.input_prompt})]}),s.jsx("button",{className:"group-hover:flex hidden",onClick:h=>{h.stopPropagation(),l(a)},children:s.jsx(P,{})}),(w==null?void 0:w.ques_id)===a.ques_id&&s.jsxs("div",{ref:y,children:[s.jsx(J,{handleDelete:g,item:a,atEnd:n.length>2&&(n[n.length-1].ques_id===a.ques_id||n[n.length-2].ques_id===a.ques_id)}),","]})]},a==null?void 0:a.ques_id)),!n.length&&s.jsx("p",{className:"pl-2 text-headGrey font-semibold text-sm",children:"No Bookmarks yet"})]})]})},os=({handleStopNewChat:e})=>{const{clearChats:n}=S(),{state:p,hideSidebar:i}=Q(),{setSession:f}=B(),{clearQuery:m}=O(),k=async()=>{i(),m(),f(""),n(),e()};return s.jsxs("section",{className:`h-[100dvh] lg:h-screen bg-white rounded-lg w-72 p-4 ${p?"flex":"hidden"} lg:flex flex-col gap-4 absolute z-40 left-0 top-0 lg:relative shadow-md lg:shadow-none`,children:[s.jsxs("div",{className:"flex flex-col items-center gap-2",children:[s.jsx("img",{src:V,alt:"logo",className:"w-28"}),s.jsx("button",{className:"bg-[#FFE4D4] text-primary w-40 h-10 rounded hover:bg-primary hover:bg-opacity-35",onClick:k,children:"+ New Chat"})]}),s.jsx("div",{className:"border border-borderGrey"}),s.jsx(K,{handleStopNewChat:e}),s.jsx("div",{className:"border border-borderGrey"}),s.jsx(W,{handleStopNewChat:e})]})};export{os as default};