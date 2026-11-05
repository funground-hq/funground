"""Spike 18: why two tf2onnx runs differ.  onnx_diff.py A.onnx B.onnx  -> what differs (weights, ops, names, metadata)."""
import sys, hashlib, onnx
from onnx import numpy_helper
a, b = (onnx.load(p) for p in sys.argv[1:3])
def wsig(m): return sorted(hashlib.sha256(numpy_helper.to_array(t).tobytes()).hexdigest() + str(t.dims) for t in m.graph.initializer)
print("initializers", len(a.graph.initializer), len(b.graph.initializer), "same weight bytes (as a multiset):", wsig(a) == wsig(b))
print("nodes", len(a.graph.node), len(b.graph.node), "same op sequence:", [n.op_type for n in a.graph.node] == [n.op_type for n in b.graph.node])
print("same op multiset:", sorted(n.op_type for n in a.graph.node) == sorted(n.op_type for n in b.graph.node))
na, nb = [n.name for n in a.graph.node], [n.name for n in b.graph.node]
print("same node names:", na == nb, "| examples differing:", [(x, y) for x, y in zip(na, nb) if x != y][:4])
print("metadata", [(p.key, p.value) for p in a.metadata_props], [(p.key, p.value) for p in b.metadata_props])
print("producer", a.producer_name, a.producer_version, "| opset", [(o.domain, o.version) for o in a.opset_import])
print("inputs", [(i.name, [d.dim_value or d.dim_param for d in i.type.tensor_type.shape.dim]) for i in a.graph.input])
print("outputs", [(i.name, [d.dim_value or d.dim_param for d in i.type.tensor_type.shape.dim]) for i in a.graph.output])
print("initializer order same:", [t.name for t in a.graph.initializer] == [t.name for t in b.graph.initializer])
print("nodes byte-identical:", sum(x.SerializeToString() == y.SerializeToString() for x, y in zip(a.graph.node, b.graph.node)), "of", len(a.graph.node))
diff = [(x, y) for x, y in zip(a.graph.node, b.graph.node) if x.SerializeToString() != y.SerializeToString()]
if diff: print("first differing node:\n", str(diff[0][0])[:600], "\n---\n", str(diff[0][1])[:600])
ia = {t.name: t for t in a.graph.initializer}; ib = {t.name: t for t in b.graph.initializer}
print("initializers byte-identical by name:", sum(ia[k].SerializeToString() == ib.get(k, onnx.TensorProto()).SerializeToString() for k in ia), "of", len(ia))
print("value_info", len(a.graph.value_info), len(b.graph.value_info), [x.name for x in a.graph.value_info] == [x.name for x in b.graph.value_info])
