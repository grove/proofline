"""Read only experiment thread consumption; never create a thread or turn."""
import json, os, selectors, signal, subprocess, sys, time
from pathlib import Path
from checks import host_probe as host

store=Path(sys.argv[1]).resolve()
threads=[]
for path in store.glob('**/events.jsonl'):
    for line in path.read_text().splitlines():
        event=json.loads(line)
        if event.get('type')=='thread.started' and event['thread_id'] not in threads:
            threads.append(event['thread_id'])
directory=Path(sys.argv[2]).resolve()
directory.mkdir(exist_ok=False)
argv=['/opt/homebrew/bin/codex','--no-daemon','app-server','--listen','stdio://','--strict-config',
    '-c','sqlite_home='+host.toml(str(directory/'state')),'-c','mcp_servers={}','-c','apps._default.enabled=false']
started=time.monotonic()
p=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
record={'model_dispatches':0,'scope':'Read-only experimental thread estimates; not observed spending',
    'argv':argv,'threads':threads,'responses':[]}
def send(value):
    p.stdin.write((json.dumps(value)+'\n').encode());p.stdin.flush()
send({'id':1,'method':'initialize','params':{'clientInfo':{'name':'proofline_usage','version':'1'},'capabilities':{'experimentalApi':True}}})
buffer=b'';request=1;index=0;errors=bytearray()
try:
    with selectors.DefaultSelector() as reader:
        reader.register(p.stdout,selectors.EVENT_READ,'out');reader.register(p.stderr,selectors.EVENT_READ,'err')
        while time.monotonic()-started<60:
            for key,_ in reader.select(1):
                chunk=os.read(key.fileobj.fileno(),65536)
                if not chunk:
                    reader.unregister(key.fileobj);continue
                if key.data=='err':
                    errors.extend(chunk[:max(0,4096-len(errors))]);continue
                buffer+=chunk
                while b'\n' in buffer:
                    line,buffer=buffer.split(b'\n',1);message=json.loads(line)
                    if message.get('id')!=request:continue
                    if request==1:
                        if 'error' in message:raise ValueError('Initialization failed')
                        send({'method':'initialized','params':{}})
                    else:
                        record['responses'].append({'thread_id':threads[index-1],
                            **({'error':message['error']} if 'error' in message else
                               {'threadUsage':message['result'].get('threadUsage')})})
                    if index==len(threads):
                        record['status']='OBSERVED';break
                    request+=1
                    send({'id':request,'method':'account/usage/read','params':{'threadId':threads[index]}})
                    index+=1
            if record.get('status')=='OBSERVED':break
        if record.get('status')!='OBSERVED':record['status']='TIMEOUT'
finally:
    try:os.killpg(p.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    p.wait();p.stdin.close();p.stdout.close();p.stderr.close()
    record.update(elapsed_seconds=time.monotonic()-started,stderr=host.redact(errors.decode(errors='replace')))
    (directory/'thread-consumption.json').write_text(json.dumps(record,indent=2)+'\n')
