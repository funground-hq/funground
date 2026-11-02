"""Adds MobileNetV4-small's flattened pre-classifier vector (the input of its last Gemm) as a second output.
    make_pooled.py MODEL_ONNX OUT_ONNX        (needs the `onnx` package; OUT_ONNX must not exist)"""
import os, sys
import onnx

src, dst = sys.argv[1:3]
assert not os.path.exists(dst)
m = onnx.load(src)
last = m.graph.node[-1]
assert last.op_type == "Gemm", last.op_type
m.graph.output.append(onnx.helper.make_tensor_value_info(last.input[0], onnx.TensorProto.FLOAT, [1, 1280]))
onnx.save(m, dst)
print("added output", last.input[0])
