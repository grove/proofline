"""Proofline-owned native input validation and explicit caller adoption.

Portable validator adapted from grove/intentline ab581c9 (Apache-2.0).
No producer module, runtime, exported inspector or model is imported/executed.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat

MAX_FILE = 2 * 1024 * 1024


def require(condition, message):
    if not condition: raise ValueError(message)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')


def sha(data): return hashlib.sha256(data).hexdigest()


def parse(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON field')
            result[key] = value
        return result
    def invalid(value): raise ValueError('Nonfinite JSON')
    value = json.loads(data.decode('utf-8'), object_pairs_hook=pairs, parse_constant=invalid)
    require(canonical(value) == data, 'Noncanonical native JSON')
    return value


def fields(value, required, optional=()):
    require(isinstance(value, dict) and set(required) <= value.keys() and value.keys() <= set(required) | set(optional), 'Missing/unexpected native fields')


def digest(value): require(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), 'Invalid native digest')


def open_directory(path):
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd); fd = new
        return fd
    except BaseException:
        os.close(fd); raise


def read_files(path):
    """Descriptor-relative bounded reads, detecting replacement and symlinks."""
    require(os.name == 'posix' and hasattr(os, 'O_NOFOLLOW') and os.open in os.supports_dir_fd, 'Secure native inspection unavailable on this host')
    raw = os.fspath(path)
    require(raw and '\\' not in raw and '//' not in raw and not any(ord(c) < 32 for c in raw) and not any(p in ('.', '..') for p in raw.split('/')), 'Unsafe bundle path')
    path = Path(os.path.abspath(raw))
    fd = open_directory(path)
    try:
        directory_identity = os.fstat(fd)
        def read(name):
            require(isinstance(name, str) and re.fullmatch('[a-zA-Z0-9][a-zA-Z0-9._-]*', name) and len(name) <= 120, 'Unsafe native filename')
            file_fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
            try:
                before = os.fstat(file_fd)
                require(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_FILE, 'Unbounded or nonregular native file')
                chunks, remaining = [], MAX_FILE + 1
                while remaining:
                    part = os.read(file_fd, min(remaining, 65536))
                    if not part: break
                    chunks.append(part);remaining -= len(part)
                data = b''.join(chunks)
                signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
                require(len(data) <= MAX_FILE and signature(before) == signature(os.fstat(file_fd)) == signature(os.stat(name, dir_fd=fd, follow_symlinks=False)), 'Native file changed during inspection')
                return data
            finally: os.close(file_fd)
        raw_manifest = read('native-manifest.json'); envelope = parse(raw_manifest)
        fields(envelope, ['record','schema_version','authorization','consumer_execution','contract_id','revision','contract_sha256','source_bundle_sha256','source_chain_sha256','continuity_sha256','requirement_ids','provenance','files'])
        require(envelope['record'] == 'intentline.native-handoff' and type(envelope['schema_version']) is int and envelope['schema_version'] == 1 and envelope['authorization'] == 'not_established' and envelope['consumer_execution'] == 'not_observed', 'Unsupported native envelope or false authorization')
        require(isinstance(envelope['files'], dict) and 4 <= len(envelope['files']) <= 1100, 'Invalid native file inventory')
        files = {}
        for name, expected in envelope['files'].items():
            digest(expected)
            require(name != 'native-manifest.json', 'Recursive marker inventory')
            data = read(name); require(sha(data) == expected, 'Native file hash mismatch: ' + name); files[name] = data
        require(sum(map(len, files.values())) <= 44 * 1024 * 1024, 'Native bundle exceeds bounded archive/active limits')
        require(read('native-manifest.json') == raw_manifest, 'Native marker changed during inspection')
        check_fd = open_directory(path)
        try:
            current = os.fstat(check_fd)
            require((current.st_dev,current.st_ino) == (directory_identity.st_dev,directory_identity.st_ino), 'Native directory identity changed')
        finally: os.close(check_fd)
        return envelope, files, sha(raw_manifest)
    finally: os.close(fd)


def sources(manifest, files, archived=False):
    version = manifest.get('schema_version')
    require(type(version) is int and version in (1,2), 'Unsupported native source generation')
    fields(manifest, ['manifest','schema_version','root','sources'] + (['predecessor','ancestors'] if version == 2 else []))
    require(manifest['manifest'] == 'intentline.sources' and isinstance(manifest['root'], str), 'Invalid source manifest')
    rows = manifest['sources']; require(isinstance(rows,list) and 1 <= len(rows) <= 64, 'Invalid source count')
    blobs, seen_context, current_seen = {}, False, False
    for i, row in enumerate(rows,1):
        fields(row, ['source_id','role','relative_path','original_location','identity','declared_authority','sha256','bytes'] + (['provenance'] if version == 2 else []), ['predecessor_source_id','predecessor_source_bundle_sha256'] if version == 2 else [])
        role = row['role']
        require(row['source_id'] == f'S{i}' and role in ('request','amendment','context') and (i == 1) == (role == 'request') and not (seen_context and role != 'context'), 'Invalid chronological sources')
        if version == 1: require(role == ('request' if i == 1 else 'context'), 'Invalid original source roles')
        seen_context |= role == 'context'
        require(row['declared_authority'] == {'request':'user_request','amendment':'operator_asserted_amendment','context':'unverified_context'}[role], 'Invalid source authority')
        if version == 2:
            require(row['provenance'] in ('current','frozen_historical'), 'Invalid source provenance')
            if row['provenance'] == 'frozen_historical':
                require(not current_seen and role != 'context' and row.get('predecessor_source_bundle_sha256') == manifest['predecessor']['source_bundle_sha256'], 'Broken historical source link')
            else:
                current_seen = True;require(role != 'request' and 'predecessor_source_id' not in row and 'predecessor_source_bundle_sha256' not in row, 'Invalid current source link')
        relative = row['relative_path']
        if relative is not None: require(isinstance(relative,str) and not relative.startswith('/') and '\\' not in relative and all(p not in ('','..','.') for p in relative.split('/')), 'Unsafe relative source path')
        digest(row['sha256']);require(type(row['bytes']) is int and 0 <= row['bytes'] <= MAX_FILE, 'Invalid source length')
        name = 'archive-' + row['sha256'] + '.txt' if archived else 'source-' + row['source_id'] + '.txt'
        require(name in files, 'Missing source capture')
        data = files[name]; require(sha(data) == row['sha256'] and len(data) == row['bytes'] and b'\0' not in data, 'Source capture mismatch/binary input')
        data.decode('utf-8');blobs[row['source_id']] = data
    require(blobs['S1'].strip() and sum(map(len,blobs.values())) <= 8 * 1024 * 1024, 'Invalid active source bundle')
    return blobs


def references(row, manifest, blobs):
    refs = row['source_refs'];require(isinstance(refs,list) and refs, 'Missing source references')
    roles = {s['source_id']:s['role'] for s in manifest['sources']}
    for ref in refs:
        fields(ref, ['source_id','line_start','line_end','quote'])
        require(ref['source_id'] in blobs and type(ref['line_start']) is int and type(ref['line_end']) is int and 1 <= ref['line_start'] <= ref['line_end'], 'Invalid source reference')
        lines = blobs[ref['source_id']].decode('utf-8').splitlines(keepends=True)
        require(ref['line_end'] <= len(lines), 'Invalid quoted line range')
        exact = ''.join(lines[ref['line_start']-1:ref['line_end']])
        require(ref['quote'] in (exact,exact.removesuffix('\n').removesuffix('\r')), 'Native quotation mismatch')
    if row.get('basis') in ('request','necessary_invariant'): require(any(roles[r['source_id']] in ('request','amendment') for r in refs), 'Request obligation has no user-source support')
    if row.get('basis') == 'project_constraint': require(any(roles[r['source_id']] == 'context' for r in refs), 'Constraint has no current context support')


def contract(value, manifest, blobs):
    fields(value, ['contract','schema_version','contract_id','revision','source_bundle_sha256','intended_outcome','requirements','constraints','out_of_scope','open_decisions','evidence_gaps','change_notes'], ['advisory_notes'])
    require(value['contract'] == 'intentline.acceptance' and type(value['schema_version']) is int and value['schema_version'] == 1 and isinstance(value['contract_id'],str) and re.fullmatch('[a-z0-9][a-z0-9-]{0,79}',value['contract_id']) and type(value['revision']) is int and 1 <= value['revision'] <= 999999, 'Unsupported native contract')
    require(value['source_bundle_sha256'] == sha(canonical(manifest)), 'Contract/source identity mismatch')
    require(isinstance(value['requirements'],list) and value['requirements'], 'Missing obligations')
    ids = []
    for row in value['requirements']:
        fields(row,['id','statement','basis','source_refs','boundaries','seam','oracle','planned_evidence','plan_state'])
        require(isinstance(row['id'],str) and re.fullmatch('R[1-9][0-9]*',row['id']) and row['id'] not in ids, 'Duplicate/invalid R ID');ids.append(row['id'])
        require(row['basis'] in ('request','project_constraint','necessary_invariant') and row['plan_state'] in ('planned','gap'), 'Invalid requirement basis/state')
        for key in ('statement','seam','oracle','planned_evidence'): require(isinstance(row[key],str) and row[key].strip(), 'Missing acceptance evidence plan')
        require(isinstance(row['boundaries'],list) and all(isinstance(x,str) and x.strip() for x in row['boundaries']), 'Invalid boundaries')
        references(row,manifest,blobs)
    for category in ('constraints','out_of_scope','open_decisions'):
        require(isinstance(value[category],list), 'Invalid contract category')
        for row in value[category]:
            required = ['statement','source_refs'] + (['basis','scope'] if category == 'constraints' else ['id','kind'] if category == 'open_decisions' else [])
            fields(row,required);require(isinstance(row['statement'],str) and row['statement'].strip(), 'Empty source obligation');references(row,manifest,blobs)
    require(isinstance(value['evidence_gaps'],list) and isinstance(value['change_notes'],list) and len(value['change_notes']) == value['revision'] and value['change_notes'][0] == {'revision':1,'kind':'initial'}, 'Invalid contract history/gaps')
    require(isinstance(value['intended_outcome'],str) and value['intended_outcome'].strip(), 'Missing intended outcome')
    if 'advisory_notes' in value: require(isinstance(value['advisory_notes'],list) and all(isinstance(n,str) and n.strip() for n in value['advisory_notes']), 'Invalid advisory notes')
    decision_ids=set()
    for row in value['constraints']: require(row['basis'] in ('request','project_constraint','necessary_invariant') and isinstance(row['scope'],str) and row['scope'].strip(), 'Invalid constraint scope/basis')
    for row in value['open_decisions']:
        require(isinstance(row['id'],str) and re.fullmatch('D[1-9][0-9]*',row['id']) and row['id'] not in decision_ids and row['kind'] in ('outcome','authority_conflict'), 'Invalid decision');decision_ids.add(row['id'])
    gap_ids=set()
    for gap in value['evidence_gaps']:
        fields(gap,['requirement_ids','reason']);require(isinstance(gap['requirement_ids'],list) and gap['requirement_ids'] and set(gap['requirement_ids']) <= set(ids) and isinstance(gap['reason'],str) and gap['reason'].strip(), 'Invalid evidence gap');gap_ids.update(gap['requirement_ids'])
    require(all(r['plan_state']!='gap' or r['id'] in gap_ids for r in value['requirements']), 'Undisclosed evidence gap')
    return ids


def revision_history(history, manifest, blobs):
    require(isinstance(history,list) and history, 'Missing exact contract history')
    historic_ids=set()
    for index,c in enumerate(history,1):
        contract(c,manifest,blobs);require(c['revision']==index, 'Invalid revision sequence')
        if index>1:
            previous=history[index-2];note=c['change_notes'][-1]
            fields(note,['revision','kind','reason','previous_contract_sha256','mappings','retired_ids','claimed_authority'])
            require(note['revision']==index and note['kind']=='revision' and note['previous_contract_sha256']==sha(canonical(previous)) and c['change_notes'][:-1]==previous['change_notes'] and c['contract_id']==previous['contract_id'], 'Changed revision identity/history')
            old={r['id']:r for r in previous['requirements']};new={r['id']:r for r in c['requirements']}
            require(not (new.keys()-old.keys())&historic_ids and len(set(note['retired_ids']))==len(note['retired_ids']) and set(note['retired_ids'])==old.keys()-new.keys(), 'Retired revision ID/accounting mismatch')
            covered=set()
            for mapping in note['mappings']:
                fields(mapping,['from','to','reason']);a,b=set(mapping['from']),set(mapping['to'])
                require(a and len(a)==len(mapping['from']) and len(b)==len(mapping['to']) and a<=old.keys() and b<=new.keys() and not covered&a, 'Invalid revision mapping')
                covered|=a
            require({i for i in old if i not in new or old[i]!=new[i]}<=covered, 'Unmapped changed/deleted requirement')
        historic_ids.update(r['id'] for r in c['requirements'])


def continuity(record, old, new, manifest, blobs, old_manifest):
    fields(record,['record','schema_version','predecessor_contract_sha256','predecessor_source_bundle_sha256','contract_sha256','source_bundle_sha256','mappings','added_requirement_ids','other_changes'])
    require(record['record'] == 'intentline.continuity' and type(record['schema_version']) is int and record['schema_version'] == 1 and new['revision'] == 1 and new['contract_id'] != old['contract_id'], 'Invalid successor continuity')
    for key,value in {'predecessor_contract_sha256':sha(canonical(old)),'predecessor_source_bundle_sha256':old['source_bundle_sha256'],'contract_sha256':sha(canonical(new)),'source_bundle_sha256':new['source_bundle_sha256']}.items(): require(record[key] == value, 'Continuity identity mismatch')
    before, after = {r['id']:r for r in old['requirements']}, {r['id']:r for r in new['requirements']}
    origins, targets = set(),set()
    source_map = {r['predecessor_source_id']:r['source_id'] for r in manifest['sources'] if r['provenance'] == 'frozen_historical'}
    for old_source in old_manifest['sources']:
        if old_source['role'] == 'context':
            match = next((r for r in manifest['sources'] if r['role'] == 'context' and r['sha256'] == old_source['sha256'] and r['relative_path'] == old_source['relative_path']),None)
            source_map[old_source['source_id']] = match['source_id'] if match else 'unavailable_historical_context'
    def remap(row):
        copied = json.loads(json.dumps(row))
        for ref in copied['source_refs']:ref['source_id'] = source_map.get(ref['source_id'],ref['source_id'])
        return copied
    def changed_support(mapping, old_rows):
        references(mapping,manifest,blobs)
        role = 'amendment' if any(r.get('basis','request') != 'project_constraint' for r in old_rows) else 'context'
        require(any(s['role'] == role and s['provenance'] == 'current' and s['source_id'] in {r['source_id'] for r in mapping['source_refs']} for s in manifest['sources']), 'Missing new change/retirement authority support')
    require(isinstance(record['mappings'],list), 'Invalid continuity mappings')
    for mapping in record['mappings']:
        fields(mapping,['from','to','disposition','reason','source_refs'])
        a,b = set(mapping['from']),set(mapping['to'])
        require(a and len(a) == len(mapping['from']) and len(b) == len(mapping['to']) and a <= before.keys() and b <= after.keys() and not (origins & a or targets & b) and isinstance(mapping['reason'],str) and mapping['reason'].strip(), 'Invalid continuity mapping')
        kind = mapping['disposition'];shapes={'preserved':len(a)==len(b)==1,'changed':len(a)==len(b)==1,'retired':not b,'split':len(a)==1 and len(b)>1,'merged':len(a)>1 and len(b)==1}
        require(kind in shapes and shapes[kind], 'Invalid continuity disposition')
        references(mapping,manifest,blobs)
        if kind == 'preserved':
            origin,destination=mapping['from'][0],mapping['to'][0]
            old_binding = {k:v for k,v in remap(before[origin]).items() if k not in ('seam','planned_evidence','plan_state')}
            new_binding = {k:v for k,v in after[destination].items() if k not in ('seam','planned_evidence','plan_state')}
            require(origin == destination and old_binding == new_binding, 'False mechanical preservation')
        else:
            changed_support(mapping,[before[i] for i in a]);require(not any(i in before and i not in a for i in b), 'Aliased inherited ID')
        origins |= a;targets |= b
    added = record['added_requirement_ids']
    require(isinstance(added,list) and len(set(added)) == len(added) and set(added) == after.keys()-targets and not set(added)&before.keys() and origins == before.keys(), 'Incomplete old/new continuity accounting')
    accounted=set()
    for mapping in record['other_changes']:
        fields(mapping,['category','from_index','to_indices','reason','source_refs'])
        category,index=mapping['category'],mapping['from_index']
        require(category in ('constraints','out_of_scope') and type(index) is int and 1 <= index <= len(old[category]) and (category,index) not in accounted and len(set(mapping['to_indices'])) == len(mapping['to_indices']) and all(type(i) is int and 1 <= i <= len(new[category]) for i in mapping['to_indices']), 'Invalid ancillary mapping')
        changed_support(mapping,[old[category][index-1]]);accounted.add((category,index))
    for category in ('constraints','out_of_scope'):
        for i,row in enumerate(old[category],1):require((category,i) in accounted or remap(row) in new[category], 'Inherited constraint/exclusion omitted')


def inspect_bundle(path):
    return inspect_payload(*read_files(path))


def inspect_payload(envelope,files,bundle_digest):
    require({'contract.json','history.json','source-manifest.json','brief.md','inspect_bundle.py'} <= files.keys(), 'Missing critical native files')
    manifest=parse(files['source-manifest.json']);blobs=sources(manifest,files)
    c=parse(files['contract.json']);ids=contract(c,manifest,blobs)
    require(files['brief.md'] == b'# Native acceptance input (authorization not established)\n\n' + canonical(c), 'Rendered native brief changed')
    history = parse(files['history.json']); revision_history(history,manifest,blobs)
    require(history[-1] == c, 'Current contract/history mismatch')
    require(not c['open_decisions'] and not c['evidence_gaps'] and all(r['plan_state']=='planned' for r in c['requirements']), 'Native accepted-input plan is not ready')
    require(all(envelope[k] == c[k] for k in ('contract_id','revision','source_bundle_sha256')) and envelope['contract_sha256'] == sha(files['contract.json']) and envelope['requirement_ids'] == ids, 'Native contract identity/inventory mismatch')
    chain = sha(canonical({'source_manifest':manifest,'ancestors':manifest.get('ancestors',[])}))
    require(envelope['source_chain_sha256'] == chain, 'Native source-chain identity mismatch')
    expected_files={'contract.json','history.json','source-manifest.json','brief.md','inspect_bundle.py'} | {'source-'+s['source_id']+'.txt' for s in manifest['sources']}
    snapshots=[]
    ancestor_ids=manifest.get('ancestors',[])
    require(isinstance(ancestor_ids,list) and len(ancestor_ids)<=8 and len(set(ancestor_ids))==len(ancestor_ids), 'Invalid ancestor bounds/duplicates')
    archive_bytes={}
    for i,snapshot_digest in enumerate(ancestor_ids):
        digest(snapshot_digest);name='archive-'+snapshot_digest+'.json';require(name in files and sha(files[name])==snapshot_digest, 'Missing/tampered predecessor')
        snapshot=parse(files[name]);fields(snapshot,['record','schema_version','manifest','history','continuity'])
        require(snapshot['record']=='intentline.predecessor' and type(snapshot['schema_version']) is int and snapshot['schema_version']==1, 'Unsupported predecessor')
        m=snapshot['manifest'];old_blobs=sources(m,files,True)
        require(m.get('ancestors',[])==ancestor_ids[i+1:] and isinstance(snapshot['history'],list) and snapshot['history'], 'Missing/unrelated ancestor links')
        revision_history(snapshot['history'],m,old_blobs)
        for row in m['sources']:
            filename='archive-'+row['sha256']+'.txt';expected_files.add(filename);archive_bytes[filename]=files[filename]
        expected_files.add(name);archive_bytes[name]=files[name];snapshots.append((snapshot,old_blobs))
    require(sum(map(len,archive_bytes.values()))<=32*1024*1024, 'Ancestor archive exceeds 32 MiB')
    pairs=[(manifest,blobs,c)] + [(s['manifest'],b,s['history'][0]) for s,b in snapshots]
    for i,(m,b,current) in enumerate(pairs):
        if m['schema_version']==1:continue
        require(i<len(snapshots), 'Missing predecessor')
        old=snapshots[i][0];last=old['history'][-1]
        identity={'contract_id':last['contract_id'],'revision':last['revision'],'contract_sha256':sha(canonical(last)),'source_bundle_sha256':sha(canonical(old['manifest'])),'snapshot_sha256':sha(canonical(old))}
        require(m['predecessor']==identity, 'Predecessor identity mismatch')
        inherited=[s for s in old['manifest']['sources'] if s['role'] in ('request','amendment')];frozen=[s for s in m['sources'] if s['provenance']=='frozen_historical']
        require(len(inherited)==len(frozen), 'Inherited source promise omitted')
        for a,z in zip(inherited,frozen):require(z['predecessor_source_id']==a['source_id'] and all(a[k]==z[k] for k in ('role','sha256','bytes','declared_authority','relative_path','original_location','identity')), 'Changed inherited source identity')
        if i==0:
            require({'continuity.json','initial-contract.json','successor-complete.json'}<=files.keys(), 'Incomplete successor publication')
            initial=parse(files['initial-contract.json']);contract(initial,m,b)
            require(initial == history[0], 'Initial successor/history mismatch')
            record=parse(files['continuity.json']); marker=parse(files['successor-complete.json'])
            require(files['successor-complete.json']==canonical({'record':'intentline.successor-complete','schema_version':1,'contract_sha256':sha(files['initial-contract.json']),'source_bundle_sha256':sha(canonical(m)),'continuity_sha256':sha(files['continuity.json'])}) and envelope['continuity_sha256']==sha(files['continuity.json']), 'Successor completion mismatch')
            expected_files |= {'continuity.json','initial-contract.json','successor-complete.json'}
        else: initial=current;record=snapshots[i-1][0]['continuity']
        continuity(record,last,initial,m,b,old['manifest'])
        historical={r['id'] for s,_ in snapshots[i:] for h in s['history'] for r in h['requirements']}
        require(not ({r['id'] for r in initial['requirements']}-{r['id'] for r in last['requirements']})&historical, 'Retired ancestor ID reused')
        require(all(initial['contract_id']!=h['contract_id'] for s,_ in snapshots[i:] for h in s['history']), 'Ancestor contract ID reused')
    if manifest['schema_version']==1:require(envelope['continuity_sha256'] is None, 'Unexpected original continuity')
    require(set(files)==expected_files, 'Unexpected/missing native payload inventory')
    fields(envelope['provenance'],['audits','adoptions','authentication'])
    require(envelope['provenance']['authentication']=='unverified', 'False provenance authentication')
    for audit in envelope['provenance']['audits']:
        fields(audit,['sha256','outcome','reported_independence','authentication']);digest(audit['sha256'])
        require(audit['outcome']=='READY_FOR_ADOPTION' and audit['authentication']=='unverified', 'Disputed or false audit provenance')
    for adoption in envelope['provenance']['adoptions']:
        fields(adoption,['sha256','approval_file_sha256','assertion','authentication']);digest(adoption['sha256']);digest(adoption['approval_file_sha256'])
        require(adoption['assertion']=='operator_asserted' and adoption['authentication']=='unverified', 'False adoption authority')
    return {'record':'intentline.native-inspection','schema_version':1,'authorization':'not_established','consumer_execution':'not_observed',
            'contract_sha256':envelope['contract_sha256'],'source_bundle_sha256':envelope['source_bundle_sha256'],
            'source_chain_sha256':chain,'bundle_sha256':bundle_digest,'requirement_ids':ids,
            'contract':c,'source_manifest':manifest,'files':envelope['files']}


def read_regular(path):
    raw=os.fspath(path)
    require(raw and '\\' not in raw and '//' not in raw and not any(ord(c)<32 for c in raw) and not any(p in ('.','..') for p in raw.split('/')), 'Unsafe native reference path')
    absolute=Path(os.path.abspath(raw));fd=open_directory(absolute.parent)
    file_fd=None
    try:
        file_fd=os.open(absolute.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
        before=os.fstat(file_fd);require(stat.S_ISREG(before.st_mode) and before.st_size<=MAX_FILE,'Native reference must be a bounded regular file')
        data=b''
        while len(data)<=MAX_FILE:
            part=os.read(file_fd,min(65536,MAX_FILE+1-len(data)))
            if not part:break
            data+=part
        signature=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
        require(len(data)<=MAX_FILE and signature(before)==signature(os.fstat(file_fd))==signature(os.stat(absolute.name,dir_fd=fd,follow_symlinks=False)),'Native reference changed during read')
        check=open_directory(absolute.parent)
        try:require((os.fstat(check).st_dev,os.fstat(check).st_ino)==(os.fstat(fd).st_dev,os.fstat(fd).st_ino),'Native reference parent changed')
        finally:os.close(check)
        return data
    finally:
        if file_fd is not None:os.close(file_fd)
        os.close(fd)


def inspect_intentline(path):
    inspection=inspect_bundle(path)
    envelope,files,bundle_digest=read_files(path)
    require(bundle_digest==inspection['bundle_sha256'],'Bundle changed during native inspection')
    contract=inspection['contract'];manifest=inspection['source_manifest']
    # Preserve each exact stream in separate protected files. This display is explicitly indexed.
    source=b'# Indexed Intentline source envelope (not a verbatim single request)\n\n'
    for row in manifest['sources']:
        name='source-'+row['source_id']+'.txt'
        source+=f"Stream {row['source_id']}; role {row['role']}; SHA-256 {row['sha256']}; bytes {row['bytes']}; provenance {row.get('provenance','current_or_explicit_stdin')}\n".encode()+files[name]+b'\n\n'
    # Ancestors include historical documentary qualifications, never current permission.
    source+=b'Historical predecessor records and every original stream are preserved under intentline/. Read that full lineage when assessing continuity.\n'
    metadata={'format':'intentline-native','qualification':'experimental/offline-qualified; live not_run',
              'bundle_path':str(Path(os.path.abspath(os.fspath(path)))),'bundle_sha256':bundle_digest,
              'contract_sha256':inspection['contract_sha256'],'source_chain_sha256':inspection['source_chain_sha256'],
              'source_bundle_sha256':inspection['source_bundle_sha256'],'source_sha256':sha(source),
              'criterion_ids':inspection['requirement_ids'],'scope':'standalone','parent_completion':False,
              'product_references':[{'relative_path':s['relative_path'],'sha256':s['sha256']} for s in manifest['sources']
                                    if s['role']=='context' and s['source_id'] in {r['source_id'] for category in ('requirements','constraints','out_of_scope') for row in contract[category] for r in row['source_refs']}],
              'file_hashes':envelope['files']}
    return metadata,source.decode('utf-8'),files['brief.md'].decode('utf-8')


def adopted_intentline(path,contract_sha256,source_chain_sha256,bundle_sha256,approval_reference,
                       approval_path=None,approval_sha256=None):
    metadata,source,brief=inspect_intentline(path)
    require(all(isinstance(v,str) and v.strip() for v in (contract_sha256,source_chain_sha256,bundle_sha256,approval_reference)),
            'Exact trusted-caller native adoption is missing; an Intentline assertion, label or approval file alone cannot authorize delivery')
    require(contract_sha256==metadata['contract_sha256'] and source_chain_sha256==metadata['source_chain_sha256'] and bundle_sha256==metadata['bundle_sha256'],
            'Native contract/source-chain/bundle changed since caller adoption')
    # These flags are the existing external caller boundary, not proof of authenticated identity.
    approval={'kind':'trusted-caller-native-adoption','reference':approval_reference,'authentication':'caller_asserted_unverified'}
    if approval_path is not None:
        raw=read_regular(approval_path)
        require(sha(raw)==approval_sha256 and contract_sha256.encode() in raw and source_chain_sha256.encode() in raw,
                'Externally inspected native approval reference changed or does not bind contract and complete source chain')
        approval.update(path=str(Path(os.path.abspath(os.fspath(approval_path)))),sha256=sha(raw))
    else:require(approval_sha256 is None,'Approval digest needs its actual inspected reference file')
    metadata['approval']=approval
    return metadata,source,brief


def validate_product(metadata,repo,git_bytes):
    require(not git_bytes(repo,'status','--porcelain','--untracked-files=normal'),'Native delivery requires the unchanged clean product checkout')
    for ref in metadata['product_references']:
        path=ref['relative_path']
        # No aliases for native binding documents: exact ordinary tracked bytes only.
        raw=read_regular(Path(repo)/path)
        require(sha(raw)==ref['sha256'],'Current binding product document changed')
        mode=git_bytes(repo,'ls-tree','HEAD','--',path).decode().split()
        require(mode and mode[0] in ('100644','100755') and git_bytes(repo,'show','HEAD:'+path)==raw,
                'Native binding document must be an exact regular tracked checkout file')


def request_from(metadata):
    approval=metadata['approval']
    return {'path':metadata['bundle_path'],'contract_sha256':metadata['contract_sha256'],
            'source_chain_sha256':metadata['source_chain_sha256'],'bundle_sha256':metadata['bundle_sha256'],
            'approval_reference':approval['reference'],'approval_path':approval.get('path'),
            'approval_sha256':approval.get('sha256')}


def worker_metadata(metadata):
    result=dict(metadata)
    result.pop('bundle_path',None)
    result['approval']={'kind':'trusted-caller-native-adoption','authentication':'caller_asserted_unverified',
                        'binding_sha256':sha(canonical(metadata['approval']))}
    return result
