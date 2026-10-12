"""Desktop UI. No web server, API key or paid model calls."""
import os
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pipeline as p

class App:
    def __init__(self, root):
        self.root=root; self.job=None; self.last_video=None; self.events=queue.Queue();self.busy=False
        root.title('로컬 클립 제작기');root.geometry('1040x830')
        self.fields={}
        top=ttk.Frame(root,padding=14);top.pack(fill='both',expand=True)
        ttk.Label(top,text='링크 준비 → 구간 선택 → 제목 수정 → 영상 만들기',font=('맑은 고딕',15,'bold')).pack(anchor='w')
        ttk.Label(top,text='다운로드에는 인터넷이 필요합니다. 대사 인식·영상 편집은 이 PC에서 처리합니다.').pack(anchor='w',pady=(4,12))
        row=ttk.Frame(top);row.pack(fill='x')
        self.source=tk.StringVar();ttk.Entry(row,textvariable=self.source).pack(side='left',fill='x',expand=True)
        ttk.Button(row,text='파일 선택',command=self.select_file).pack(side='left',padx=4)
        self.prepare_btn=ttk.Button(row,text='1. 원본·대사 준비',command=self.prepare);self.prepare_btn.pack(side='left')
        row=ttk.Frame(top);row.pack(fill='x',pady=8)
        ttk.Label(row,text='대사 인식 모델').pack(side='left')
        self.model=tk.StringVar(value='small')
        ttk.Combobox(row,textvariable=self.model,values=['base','small','medium'],width=10,state='readonly').pack(side='left',padx=8)
        ttk.Label(row,text='base 빠름 / small 기본 / medium 느리지만 더 정밀').pack(side='left')
        ttk.Button(row,text='기존 작업 열기',command=self.open_job).pack(side='right')
        ttk.Label(top,text='자동 후보 — 대사 키워드로 고른 초안입니다. 재미와 시작·종료점은 직접 확인하세요.').pack(anchor='w')
        self.table=ttk.Treeview(top,columns=('range','text'),show='headings',height=5)
        self.table.heading('range',text='원본 구간');self.table.heading('text',text='인식된 대사')
        self.table.column('range',width=145,stretch=False);self.table.column('text',width=780)
        self.table.pack(fill='x',pady=6);self.table.bind('<<TreeviewSelect>>',self.choose)
        actions=ttk.Frame(top);actions.pack(fill='x')
        ttk.Button(actions,text='원본 보기',command=self.open_source).pack(side='left')
        ttk.Button(actions,text='후보 구간 재생',command=lambda:self.open_artifact('review.html')).pack(side='left',padx=6)
        ttk.Button(actions,text='전체 대사 보기',command=lambda:self.open_artifact('transcript.txt')).pack(side='left',padx=6)
        ttk.Button(actions,text='AI 검토용 요약 열기',command=lambda:self.open_artifact('review-brief.md')).pack(side='left')
        form=ttk.LabelFrame(top,text='2. 편집 내용',padding=10);form.pack(fill='x',pady=10)
        for i,(key,label,default) in enumerate([
            ('start','시작 (초 또는 분:초)','0'),('end','종료 (초 또는 분:초)','22'),
            ('title1','제목 첫째 줄','업무 부탁했다가'),('title2','제목 둘째 줄','눈치 보게 된 이유'),
            ('series','상단 작은 문구','하이라이트'),('credit','출처','')]):
            ttk.Label(form,text=label).grid(row=i,column=0,sticky='w',padx=(0,12),pady=3)
            self.fields[key]=tk.StringVar(value=default)
            ttk.Entry(form,textvariable=self.fields[key]).grid(row=i,column=1,sticky='ew')
        form.columnconfigure(1,weight=1)
        ttk.Label(form,text='상황 자막 (한 줄에 하나, 빈칸이면 생략 / 클립 길이를 균등하게 나눠 표시)').grid(row=6,column=0,columnspan=2,sticky='w',pady=(8,3))
        self.captions=tk.Text(form,height=3,font=('맑은 고딕',11));self.captions.grid(row=7,column=0,columnspan=2,sticky='ew')
        row=ttk.Frame(top);row.pack(fill='x')
        self.render_btn=ttk.Button(row,text='3. 세로 영상 만들기',command=self.render);self.render_btn.pack(side='left')
        ttk.Button(row,text='완성본 재생',command=self.play).pack(side='left',padx=6)
        ttk.Button(row,text='작업 폴더',command=lambda:os.startfile(str(self.job or p.ROOT))).pack(side='left')
        ttk.Button(row,text='샘플 편집 설정 불러오기',command=self.load_sample).pack(side='right')
        self.status=tk.StringVar(value='준비됨');ttk.Label(top,textvariable=self.status,wraplength=980).pack(anchor='w',pady=10)
        ttk.Label(top,text='게시·업로드 기능은 없습니다. 원본 이용 조건을 확인하고 완성본은 직접 검수하세요.',foreground='#666').pack(anchor='w')
        root.after(100,self.poll)

    def select_file(self):
        f=filedialog.askopenfilename(filetypes=[('영상','*.mp4 *.mkv *.mov *.webm'),('모든 파일','*.*')])
        if f:self.source.set(f)

    def background(self,fn,kind):
        if self.busy:return
        self.busy=True;self.prepare_btn.configure(state='disabled');self.render_btn.configure(state='disabled')
        def worker():
            try:self.events.put((kind,fn()))
            except Exception as e:self.events.put(('error',str(e)))
            finally:self.events.put(('done',None))
        threading.Thread(target=worker,daemon=True).start()

    def log(self,s):self.events.put(('log',s))

    def poll(self):
        try:
            while True:
                kind,value=self.events.get_nowait()
                if kind=='log':self.status.set(value)
                elif kind=='prepared':self.show_job(value)
                elif kind=='rendered':self.last_video=value;self.status.set(f'완성: {value}')
                elif kind=='error':self.status.set('오류 — 내용을 확인하세요.');messagebox.showerror('작업 오류',value)
                elif kind=='done':
                    self.busy=False;self.prepare_btn.configure(state='normal');self.render_btn.configure(state='normal')
        except queue.Empty:pass
        self.root.after(100,self.poll)

    def prepare(self):
        source=self.source.get().strip();model=self.model.get()
        if source:self.background(lambda:p.prepare(source,model,self.log),'prepared')

    def show_job(self,job):
        self.job=Path(job);meta=p.read_json(self.job/'source.json');self.candidates=p.read_json(self.job/'candidates.json')
        self.source.set(meta.get('input') or meta.get('url') or meta['file'])
        self.table.delete(*self.table.get_children())
        for i,c in enumerate(self.candidates):self.table.insert('', 'end',iid=str(i),values=(f'{p.stamp(c["start"])} – {p.stamp(c["end"])}',c['text']))
        self.fields['credit'].set('출처  '+meta['uploader']);self.fields['series'].set('하이라이트')
        self.status.set(f'준비 완료: {meta["title"]}. 후보를 선택하거나 원하는 시간을 직접 입력하세요.')

    def open_job(self):
        f=filedialog.askopenfilename(initialdir=p.JOBS,title='source.json 선택',filetypes=[('작업 정보','source.json')])
        if f:
            try:self.show_job(Path(f).parent)
            except Exception as e:messagebox.showerror('작업 열기',str(e))

    def choose(self,event=None):
        if self.table.selection():
            c=self.candidates[int(self.table.selection()[0])]
            self.fields['start'].set(str(c['start']));self.fields['end'].set(str(c['end']))
            self.fields['title1'].set('제목을 입력하세요');self.fields['title2'].set('장면의 핵심을 짧게')
            self.captions.delete('1.0','end')
            self.status.set(c['text'])

    def open_artifact(self,name):
        if self.job and (self.job/name).exists():os.startfile(str(self.job/name))

    def open_source(self):
        if self.job:os.startfile(p.read_json(self.job/'source.json')['file'])

    def load_sample(self):
        self.job=None
        spec=p.read_json(p.ROOT/'sample-edit.json')
        self.source.set(spec['source'])
        for key in ('start','end','series','credit'):self.fields[key].set(str(spec[key]))
        self.fields['title1'].set(spec['title'][0]);self.fields['title2'].set(spec['title'][1])
        self.captions.delete('1.0','end');self.captions.insert('1.0','\n'.join(c['text'] for c in spec['captions']))
        self.status.set('샘플 설정을 불러왔습니다. 바로 영상 만들기를 누를 수 있습니다.')

    def render(self):
        try:
            start,end=(p.parse_time(self.fields[k].get()) for k in ('start','end'))
            source=self.source.get().strip()
            if not Path(source).is_file():
                if not self.job:raise ValueError('원본·대사 준비를 먼저 실행하세요.')
                meta=p.read_json(self.job/'source.json')
                if source and source not in (meta.get('url'),meta.get('input')):raise ValueError('입력 링크가 바뀌었습니다. 원본·대사 준비를 먼저 실행하세요.')
                source=meta['file']
            texts=[s.strip() for s in self.captions.get('1.0','end').splitlines() if s.strip()]
            captions=[{'start':round(i*(end-start)/len(texts),3),'end':round((i+1)*(end-start)/len(texts),3),'text':s} for i,s in enumerate(texts)]
            spec={'source':str(Path(source).resolve()),'start':start,'end':end,
                  'title':[self.fields['title1'].get(),self.fields['title2'].get()],
                  'series':self.fields['series'].get(),'credit':self.fields['credit'].get(),'captions':captions}
            p.validate_spec(spec)
            self.background(lambda:p.render(spec,p.ROOT/'renders',self.log),'rendered')
        except Exception as e:messagebox.showerror('편집 내용 확인',str(e))

    def play(self):
        if self.last_video:os.startfile(str(self.last_video))

if __name__=='__main__':
    root=tk.Tk();App(root);root.mainloop()
