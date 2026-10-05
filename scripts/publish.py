import hashlib,json,os,re,urllib.request,urllib.error,urllib.parse
from pathlib import Path

def validate(directory,tag):
    if not re.fullmatch(r'v(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)',tag):
        raise ValueError('Invalid firmware tag')
    version=tag[1:]
    names=[f'alpaca-printer-esp32-{version}-ota.bin',f'alpaca-printer-esp32-{version}-full.bin','alpaca-fonts-0x410000.bin']
    expected=set(names+['SHA256SUMS.txt'])
    if {p.name for p in directory.iterdir()} != expected or any(not p.is_file() or p.is_symlink() for p in directory.iterdir()):
        raise ValueError('Only firmware images, font and checksums may be published')
    records={}
    for row in (directory/'SHA256SUMS.txt').read_text().splitlines():
        match=re.fullmatch(r'([0-9a-f]{64})  (.+)',row)
        if not match or match[2] in records:raise ValueError('Invalid checksum list')
        records[match[2]]=match[1]
    if set(records)!=set(names):raise ValueError('Checksum file must list exactly the three images')
    for name in names:
        if hashlib.sha256((directory/name).read_bytes()).hexdigest()!=records[name]:raise ValueError('Checksum mismatch: '+name)
    app=(directory/names[0]).read_bytes();full=(directory/names[1]).read_bytes();font=(directory/names[2]).read_bytes()
    if not 32<=len(app)<=0x200000 or app[0]!=0xe9 or int.from_bytes(app[12:14],'little')!=9:raise ValueError('Invalid ESP32-S3 OTA image')
    if not 0<len(font)<=0x200000 or len(full)>0x800000:raise ValueError('Image exceeds flash layout')
    if full[0x10000:0x10000+len(app)]!=app or full[0x410000:0x410000+len(font)]!=font:raise ValueError('Full image differs from OTA/font')
    return names+['SHA256SUMS.txt']

def main():
    ref=os.environ.get('GITHUB_REF_NAME','')
    prefix,tag=ref.split('/',1)
    if prefix not in ['incoming','verify']:raise ValueError('Not a release/verification branch')
    directory=Path('dist');names=validate(directory,tag)
    if prefix=='verify':
        print('Verified artifact transfer, exact file list, ESP32-S3 image and all SHA-256 checks; no release created')
        return
    repo=os.environ['GITHUB_REPOSITORY'];token=os.environ['GH_TOKEN']
    headers={'Authorization':'Bearer '+token,'User-Agent':'alpaca-release-publisher','Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}
    def request(url,method='GET',data=None,content_type='application/json'):
        raw=None if data is None else json.dumps(data).encode() if content_type=='application/json' else data
        req=urllib.request.Request(url,data=raw,method=method,headers={**headers,**({'Content-Type':content_type} if raw is not None else {})})
        with urllib.request.urlopen(req,timeout=120) as response:return json.load(response)
    api='https://api.github.com/repos/'+repo
    try:release=request(api+'/releases/tags/'+tag)
    except urllib.error.HTTPError as error:
        if error.code!=404:raise
        release=request(api+'/releases','POST',{'tag_name':tag,'target_commitish':os.environ['GITHUB_SHA'],'name':tag,'draft':True,'prerelease':False,'body':'ESP32-S3 firmware. OTA updates use the -ota.bin asset; source is maintained separately in a private repository.'})
    existing={a['name']:a for a in release['assets']}
    for name in names:
        raw=(directory/name).read_bytes();digest='sha256:'+hashlib.sha256(raw).hexdigest()
        asset=existing.get(name)
        if asset is None:
            if not release['draft']:raise ValueError('Published release is incomplete; do not overwrite it')
            url=release['upload_url'].split('{')[0]+'?name='+urllib.parse.quote(name)
            asset=request(url,'POST',raw,'application/octet-stream')
        if asset['state']!='uploaded' or asset['size']!=len(raw) or asset.get('digest')!=digest:raise ValueError('Uploaded asset differs: '+name)
    if set(existing)-set(names):raise ValueError('Unexpected assets in release')
    if release['draft']:request(api+'/releases/'+str(release['id']),'PATCH',{'draft':False,'prerelease':False,'make_latest':'true'})
    print('Published and SHA-256 verified: '+tag)

if __name__=='__main__':main()
