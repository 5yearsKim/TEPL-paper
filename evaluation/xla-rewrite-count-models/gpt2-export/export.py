"""Lower public GPT-2 to HLO using abstract runtime weights; no execution."""
import argparse
import hashlib
import importlib.metadata
import inspect
import json
import os
from pathlib import Path
import shutil
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--dependency-dir', type=Path, required=True)
args = parser.parse_args()
# Keep the existing JAX/Flax/NumPy environment ahead of isolated extra packages.
sys.path.append(str(args.dependency_dir.resolve()))
os.environ.setdefault('JAX_PLATFORMS', 'cpu')
os.environ.setdefault('USE_TORCH', '0')
os.environ.setdefault('USE_TF', '0')
os.environ.setdefault('USE_FLAX', '1')

import flax
import jax
import jax.numpy as jnp
import numpy
import transformers
from transformers import GPT2Config, FlaxGPT2LMHeadModel

out = Path(__file__).resolve().parent
config_path = out / 'config.json'
config = GPT2Config.from_json_file(str(config_path))
assert (config.n_layer, config.n_head, config.n_embd, config.vocab_size) == (12, 12, 768, 50257)
batch, length = 1, 16
model = FlaxGPT2LMHeadModel(config, input_shape=(batch, length), dtype=jnp.float32, _do_init=False)
params = model.params_shape_tree
tokens = jax.ShapeDtypeStruct((batch, length), jnp.int32)


def forward(weights, input_ids, attention_mask, position_ids):
    return model(input_ids, attention_mask=attention_mask, position_ids=position_ids,
                 params=weights, train=False, return_dict=False,
                 output_attentions=False, output_hidden_states=False)[0]


lowered = jax.jit(forward).lower(params, tokens, tokens, tokens)
hlo_path = out / 'gpt2_b1_l16_f32.hlo'
hlo_path.write_text(lowered.compiler_ir('hlo').as_hlo_text())
(out / 'effective-config.json').write_text(config.to_json_string(use_diff=False))
source = out / 'source'
source.mkdir(exist_ok=True)
sources = {}
for name in ['transformers.models.gpt2.modeling_flax_gpt2',
             'transformers.models.gpt2.configuration_gpt2',
             'transformers.modeling_flax_utils', 'transformers.modeling_flax_outputs',
             'transformers.modeling_flax_pytorch_utils', 'transformers.activations']:
    module_path = args.dependency_dir / (name.replace('.', '/') + '.py')
    if module_path.is_file():
        shutil.copy2(module_path, source / module_path.name)
        sources[name] = hashlib.sha256(module_path.read_bytes()).hexdigest()
deps = sorted(f'{d.metadata["Name"]}=={d.version}' for d in importlib.metadata.distributions(path=[str(args.dependency_dir)]))
(out / 'extra-dependencies.txt').write_text('\n'.join(deps) + '\n')
leaves = jax.tree_util.tree_leaves(params)
manifest = dict(
    model='Hugging Face FlaxGPT2LMHeadModel, standard GPT-2 small architecture',
    config_url='https://huggingface.co/openai-community/gpt2/resolve/607a30d783dfa663caf39e06633721c8d4cfcd7e/config.json',
    config_sha256=hashlib.sha256(config_path.read_bytes()).hexdigest(),
    source_url='https://github.com/huggingface/transformers/blob/v4.55.4/src/transformers/models/gpt2/modeling_flax_gpt2.py',
    batch=batch, sequence_length=length, dtype='float32',
    layers=config.n_layer, heads=config.n_head, hidden_width=config.n_embd,
    vocabulary=config.vocab_size, max_positions=config.n_positions,
    parameter_count=sum(int(numpy.prod(x.shape)) for x in leaves),
    parameter_tensors=len(leaves),
    parameters='Abstract shape/dtype tree lowered as runtime arguments; no initialized or pretrained weights',
    inputs='Runtime parameters, token IDs, attention mask, and position IDs',
    mode='Deterministic forward logits, no KV cache, no generation loop',
    numerical_executions=0, pretrained_weight_downloads=0,
    versions=dict(python=sys.version.split()[0], jax=jax.__version__, flax=flax.__version__,
                  numpy=numpy.__version__, transformers=transformers.__version__),
    source_hashes=sources, hlo_sha256=hashlib.sha256(hlo_path.read_bytes()).hexdigest(),
    hlo_bytes=hlo_path.stat().st_size)
(out / 'provenance.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({k: manifest[k] for k in ['model', 'parameter_count', 'parameter_tensors', 'hlo_bytes', 'versions']}, indent=2))
