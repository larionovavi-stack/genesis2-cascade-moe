import shutil, sys, os, zipfile

# Auto-detect dataset path (different in interactive vs API mode)
D1 = '/kaggle/input/genesis2-cascade-moe-model'
D2 = '/kaggle/input/datasets/alexanderlar/genesis2-cascade-moe-model'
D = D1 if os.path.isdir(D1) else D2
W = '/kaggle/working'

for f in ['genesis2_gen.py', 'genesis2_core.py', 'neuron_embedding.py', 'vocab.json']:
    src = os.path.join(D, f)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(W, f))
        print('OK: ' + f)
# DO NOT copy embedding/ folder - we use NativeEmbeddingEngine (HashEncoder) instead
print('All files ready! Dataset path: ' + D)

if '/kaggle/working' not in sys.path:
    sys.path.insert(0, '/kaggle/working')
os.chdir('/kaggle/working')

import time, torch, gradio as gr
from neuron_embedding import NeuronPoolEmbedding, HashEncoder

class NativeEmbeddingEngine:
    def __init__(self):
        self.hash_encoder = HashEncoder(dim=384)
        self.dim = 384
    def encode(self, text):
        return self.hash_encoder.encode(text)
    def encode_batch(self, texts):
        return torch.stack([self.encode(t) for t in texts])

print('Loading native embedding (HashEncoder, dim=384)...')
emb_engine = NativeEmbeddingEngine()

from genesis2_gen import CascadeGenerator

print('Loading Genesis 2...')
t0 = time.time()
generator = CascadeGenerator(emb_engine)
generator.load_state(os.path.join(D, 'genesis2_trained_full.pt'))
elapsed = time.time() - t0
print('Loaded in ' + str(round(elapsed, 1)) + 's — ' + str(len(generator.routes)) + ' experts, ' + str(len(generator.neurons)) + ' neurons')

# Questions stored verbatim take the exact-match fast path in genesis2_gen.py and
# return a stored answer without running the cascade. The demo says which path you
# got rather than passing a lookup off as inference.
STORED = set()
for _r in generator.routes.values():
    _t = _r.get('input_text', '')
    if isinstance(_t, str):
        STORED.add(_t.lower().strip())
print('exact-match table: ' + str(len(STORED)) + ' stored questions')

def respond(message, history):
    if not message.strip():
        return ''
    is_lookup = message.lower().strip() in STORED
    t0 = time.time()
    result = generator.generate(message, top_k=5, depth=2)
    elapsed = time.time() - t0
    response = result.get('response', 'No response')
    exec_data = result.get('exec')
    cmd = ''
    if exec_data is not None:
        if isinstance(exec_data, dict):
            cmd = exec_data.get('cmd', '')
        elif isinstance(exec_data, str):
            cmd = exec_data
    if cmd.strip():
        if len(cmd) > 500:
            cmd = cmd[:500] + '...'
        response += '\n\n--- Exec command ---\n' + cmd
    ms = str(int(elapsed * 1000))
    if is_lookup:
        path = 'exact match - stored answer returned, cascade NOT used'
    else:
        path = 'cascade over ' + str(result.get('neurons_activated', 0)) + ' neurons'
    response += '\n\n[' + ms + 'ms | ' + path + ' | CPU only]'
    return response

DESC = ('Plain-language sysadmin and networking questions in, shell commands out. '
        'CPU only, no GPU, no external model weights. '
        'Measured on held-out queries: 38 of 49 correct (78%), 276 ms median - '
        'benchmark_honest.py in the repo produces that number and separates real '
        'cascade answers from exact-match lookups. Each reply below tells you which one you got.')

demo = gr.ChatInterface(respond, title='Genesis 2 - Cascade MoE', description=DESC,
                        examples=['how much free space is left on the root partition',
                                  'list the current firewall rules',
                                  'scan a subnet for live hosts',
                                  'проверить конфигурацию nginx на ошибки',
                                  'поднять туннель WireGuard и проверить'])
_app, local_url, share_url = demo.launch(share=True, prevent_thread_lock=True)

# Write share URL to GitHub Gist
if share_url:
    print('SHARE URL: ' + share_url)
    try:
        import urllib.request, json
        gist_id = 'd9bdc484813df7cb488a842cb4a0cd62'
        gh_token = os.environ.get('GH_GIST_TOKEN', '')
        if gh_token:
            content = share_url + '\nUpdated: ' + time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())
            data = json.dumps({'files': {'genesis2_demo_link.txt': {'content': content}}}).encode()
            req = urllib.request.Request('https://api.github.com/gists/' + gist_id, data=data, method='PATCH')
            req.add_header('Authorization', 'token ' + gh_token)
            req.add_header('Content-Type', 'application/json')
            resp = urllib.request.urlopen(req)
            print('Gist updated with share URL!')
        else:
            print('No GH_GIST_TOKEN set, skipping Gist update')
    except Exception as e:
        print('Failed to update gist: ' + str(e))
else:
    print('No share URL generated')

print('Demo is running. Keeping alive for 12 hours...')
time.sleep(43200)
